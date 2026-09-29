"""One self-healing browser driver for every script that touches the live shop.

Two real defects were found the hard way, and this module exists so neither has
to be re-discovered:

  1. Chrome refuses to start when the profile holds a SingletonLock from a dead
     process (exit 21, "Failed to create ... SingletonLock: File exists").
  2. Worse, and the actual cause of a total outage: agent-browser leaves headless
     Chrome RUNNING after a script exits. Those orphans hold the profile lock, so
     every subsequent browser run — the standing checkout probe, the dashboard
     read, anything — fails before it starts. On 2026-09-30 the gumroad profile
     had orphan PIDs 458116 and 561741 both alive on it, and the whole browser
     side of the queue was dead while every non-browser check still said "ok".

So: reap our own orphans (matched by the exact --user-data-dir, so the user's
real browser can never be touched), then clear lock symlinks, then launch.
"""
from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path

ROOT = "/home/john-douglas"
AB = ROOT + "/.npm/_npx/ad6c181e5b604bdb/node_modules/agent-browser/bin/agent-browser.js"
STATE = Path(ROOT) / "claimgate" / "state"
GUMROAD_PROFILE = str(STATE / "gumroad-profile")
BUYER_PROFILE = str(STATE / "buyer-profile")
FLAGS = "--no-sandbox,--disable-dev-shm-usage"
OUR_PROFILES = (GUMROAD_PROFILE, BUYER_PROFILE)


def _pids_for_profile(profile: str) -> list[int]:
    """PIDs of Chrome processes started against exactly this profile dir."""
    needle = f"--user-data-dir={profile}"
    out = subprocess.run(["pgrep", "-f", "--", needle],
                         capture_output=True, text=True).stdout
    pids = []
    me = os.getpid()
    for ln in out.split():
        try:
            pid = int(ln)
        except ValueError:
            continue
        if pid == me:
            continue
        # never kill anything that is not one of our chromium profiles
        try:
            cmd = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace")
        except OSError:
            continue
        if needle in cmd and "chrome" in cmd:
            pids.append(pid)
    return pids


def reap_orphans(profile: str, *, grace: float = 3.0) -> list[int]:
    """Kill our own leftover Chrome for this profile. Returns the PIDs killed.

    Scoped to the exact --user-data-dir string, which only this project uses, so
    the user's own browser is never a candidate.
    """
    pids = _pids_for_profile(profile)
    if not pids:
        return []
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    deadline = time.time() + grace
    while time.time() < deadline and _pids_for_profile(profile):
        time.sleep(0.3)
    for pid in _pids_for_profile(profile):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    time.sleep(0.5)
    return pids


def clear_stale_locks(profile: str) -> None:
    """Drop lock symlinks once no Chrome of ours holds them."""
    if _pids_for_profile(profile):
        return
    for n in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        p = Path(profile) / n
        try:
            if p.is_symlink() or p.exists():
                p.unlink()
        except OSError:
            pass


_REAPED: set[str] = set()


def ab(*args, profile: str, session: str, timeout: int = 300,
       reap: bool = True) -> str:
    """Run agent-browser against a clean, ours-only profile. Noise stripped.

    Leftovers are reaped at most ONCE per profile per process. Reaping on every
    call is wrong: the browser launched by the `open` step looks exactly like an
    orphan to the `eval` step that follows it, so every eval returned empty and
    the standing probe reported three doors broken that were fine. The stale lock
    is always from a previous run, so one reap at the start is the whole job.
    """
    if reap and profile not in _REAPED:
        _REAPED.add(profile)
        reap_orphans(profile)
    clear_stale_locks(profile)
    cmd = ["node", AB, "--profile", profile, "--session", session,
           "--args", FLAGS] + [str(a) for a in args]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    out = (p.stdout or "") + (p.stderr or "")
    return "\n".join(ln for ln in out.splitlines() if not ln.startswith("⚠"))


def open_and_read(url: str, *, profile: str, session: str, wait: float = 11.0,
                  limit: int = 2500) -> str:
    """Open a URL and return its visible text, whitespace-collapsed."""
    ab("open", url, profile=profile, session=session)
    time.sleep(wait)
    js = ("document.body.innerText.replace(/\\n{3,}/g,'\\n').slice(0,%d)" % limit)
    return ab("eval", js, profile=profile, session=session, reap=False)
