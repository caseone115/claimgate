import pathlib
p = pathlib.Path("scripts/check_mcpb_artifact.py")
t = p.read_text()

start = t.index("def _ensure_mcp(")
end = t.index("def check_variant(")
new = '''def _suite_command(python_exe: str, suite: pathlib.Path,
                   server: pathlib.Path) -> list[str] | None:
    """A command that runs `suite` with the MCP SDK importable, or None.

    Three real traps, all of which produced a false red on a release run:

      1. The suite imports `mcp.client.session`, so probing `import mcp` is not
         enough. This repository has a directory called `mcp/`, and Python puts
         the working directory on sys.path - so `import mcp` succeeds against
         the LOCAL FOLDER while the SDK is not installed at all. The probe has to
         name the submodule that is actually needed.
      2. A uv ephemeral environment has no pip, so "install it and try again"
         cannot be the only recovery.
      3. `uv run --with mcp` is the one form that works both on this box and in
         the workflow, so it is tried before pip.
    """
    def works(cmd: list[str]) -> bool:
        probe = subprocess.run(
            cmd + ["-c", "import mcp.client.session"], capture_output=True,
            text=True, timeout=300)
        return probe.returncode == 0

    direct = [python_exe]
    if works(direct):
        return direct + [str(suite), "--python", python_exe, "--server",
                         str(server)]

    via_uv = ["uv", "run", "--with", "mcp", "--python", python_exe, "python"]
    if works(via_uv):
        return via_uv + [str(suite), "--python", python_exe, "--server",
                         str(server)]

    subprocess.run([python_exe, "-m", "pip", "install", "--quiet", "mcp"],
                   capture_output=True, text=True)
    if works(direct):
        return direct + [str(suite), "--python", python_exe, "--server",
                         str(server)]
    return None


'''
p.write_text(t[:start] + new + t[end:])

# swap the call site
old_call = '''    p = subprocess.run(
        [python_exe, str(ROOT / v["suite"]), "--python", python_exe,
         "--server", str(server)],
        capture_output=True, text=True, timeout=1800)
    tail = [l.strip() for l in p.stdout.splitlines() if "passed," in l]
    ok(f"{v['name']}: the packed server passes its own stdio suite",
       p.returncode == 0, tail[-1] if tail else p.stderr[-300:])'''
new_call = '''    cmd = _suite_command(python_exe, ROOT / v["suite"], server)
    if cmd is None:
        ok(f"{v['name']}: the packed server passes its own stdio suite", False,
           "no interpreter here can import mcp.client.session - a fault in THIS "
           "CHECK, not in the bundle")
        return
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    tail = [l.strip() for l in p.stdout.splitlines() if "passed," in l]
    ok(f"{v['name']}: the packed server passes its own stdio suite",
       p.returncode == 0, tail[-1] if tail else p.stderr[-300:])'''
assert old_call in t, "call site not found"
t2 = pathlib.Path("scripts/check_mcpb_artifact.py").read_text()
assert old_call in t2
pathlib.Path("scripts/check_mcpb_artifact.py").write_text(
    t2.replace(old_call, new_call, 1))

# drop the old top-level guard, now per-variant
t3 = pathlib.Path("scripts/check_mcpb_artifact.py").read_text()
old_guard = '''    if not _ensure_mcp(a.python):
        print("  x the MCP SDK is not importable by "
              f"{a.python} and could not be installed - this is a fault in THIS "
              "CHECK, not in the bundles, and the run is not reported as clean")
        return 1
'''
assert old_guard in t3
pathlib.Path("scripts/check_mcpb_artifact.py").write_text(
    t3.replace(old_guard, "", 1))
print("patched")
