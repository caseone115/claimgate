# Shared by the MCP bundle build and the release step. Kept in one file rather
# than duplicated in the workflow so the version stamped into the bundle and
# the hash printed for the registry entry cannot drift apart.

import hashlib
import json
import os
import pathlib
import re
import shutil
import zipfile


# Exactly the modules server.py imports. Anything else in claimgate/ is a
# different concern (the CLI, the starter kit, outreach, the inbox) and has no
# business travelling with a published artifact.
SERVER_MODULES = ("__init__.py", "claims.py", "policy.py", "substantiation.py",
                  "htmltext.py")


def build(dist: pathlib.Path = pathlib.Path("dist")) -> pathlib.Path:
    ref = os.environ.get("GITHUB_REF_NAME", "")
    man_path = pathlib.Path("mcp") / "manifest.json"
    ver = ref.lstrip("v") or json.loads(man_path.read_text())["version"]
    root = dist / "bundle"
    if root.exists():
        shutil.rmtree(root)
    (root / "server" / "claimgate").mkdir(parents=True)
    # An explicit allowlist, not a directory copy. Copying the whole package
    # pulled outreach.py (hand-written messages and prospect addresses) and
    # inbox.py (mailbox logic) into a PUBLISHED release artifact - the same
    # class of leak as the prospect ledger that once sat in this public repo.
    # The server needs five modules; it ships five modules.
    for name in SERVER_MODULES:
        shutil.copy2(pathlib.Path("claimgate") / name,
                     root / "server" / "claimgate" / name)
    for name in ("server.py", "pyproject.toml"):
        shutil.copy2(pathlib.Path("mcp") / name, root / "server" / name)
    man = json.loads(man_path.read_text())
    man["version"] = ver
    (root / "manifest.json").write_text(json.dumps(man, indent=2) + "\n")
    out = dist / f"claimgate-{ver}.mcpb"
    # Deterministic on purpose. The MCP Registry entry pins the SHA-256 of this
    # file, so a rebuild that produced a different hash would make the entry
    # unverifiable and force the hash to be edited by hand every time. Fresh
    # mtimes on the rewritten manifest were doing exactly that. Entry
    # timestamps are normalised and the order is sorted, so the same inputs
    # give the same bytes on any machine and on any day.
    stamp = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            info = zipfile.ZipInfo(str(p.relative_to(root)), date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, p.read_bytes())
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"artifact: {out}")
    print(f"size: {out.stat().st_size} bytes")
    print(f"sha256: {digest}")
    print(f"::notice::server.json fileSha256 must be {digest}")
    _refuse_if_carried_names(root)
    return out


# Anything shaped like an email address, except the project's own support
# address, has no business in a published artifact. This is a hard stop rather
# than a warning: the cost of a false positive is one build, and the cost of a
# false negative is a stranger's address in a public download.
_ALLOWED_ADDRESSES = {"teeter.ai.bot@gmail.com"}
_ADDR = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _refuse_if_carried_names(root: pathlib.Path) -> None:
    found: list[str] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix not in (".py", ".json", ".toml", ".txt", ".md"):
            continue
        try:
            text = p.read_text(errors="replace")
        except OSError:
            continue
        for addr in _ADDR.findall(text):
            if addr.lower() not in _ALLOWED_ADDRESSES:
                found.append(f"{p.relative_to(root)}: {addr}")
    if found:
        raise SystemExit(
            "refusing to pack: the bundle carries address(es) that are not the "
            "project's own support address:\n  " + "\n  ".join(found))


if __name__ == "__main__":
    build()
