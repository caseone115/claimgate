import pathlib
p = pathlib.Path("scripts/check_mcpb_artifact.py")
t = p.read_text()

old = "def check_variant(v: dict, python_exe: str, workdir: pathlib.Path) -> None:"
new = '''def _ensure_mcp(python_exe: str) -> bool:
    """Is the MCP SDK importable by python_exe? The stdio suites need it.

    This bit the v0.1.0 run: the workflow step ran under `uv run --with
    jsonschema`, so there was no `mcp` in that environment, and both packed
    servers reported "the packed server passes its own stdio suite: FAIL" with
    ModuleNotFoundError underneath - a dependency missing from the CHECK, not
    a fault in the bundle. The checker now installs it itself when it is
    absent, so the step cannot be misconfigured into a false red.
    """
    have = subprocess.run([python_exe, "-m", "pip", "show", "mcp"],
                          capture_output=True, text=True)
    if have.returncode == 0:
        probe = subprocess.run([python_exe, "-m", "pip", "--version"],
                               capture_output=True, text=True)
        if probe.returncode != 0:
            return False
    print("  ... ensuring the MCP SDK is available for the stdio suites")
    inst = subprocess.run([python_exe, "-m", "pip", "install", "--quiet", "mcp"],
                          capture_output=True, text=True)
    return inst.returncode == 0


def check_variant(v: dict, python_exe: str, workdir: pathlib.Path) -> None:'''
assert old in t
t = t.replace(old, new, 1)

old2 = '    print("=== the PACKED MCP bundles, checked as a user would receive them ===")'
new2 = '''    print("=== the PACKED MCP bundles, checked as a user would receive them ===")
    if not _ensure_mcp(a.python):
        print("  x the MCP SDK is not importable by "
              f"{a.python} and could not be installed - this is a fault in THIS "
              "CHECK, not in the bundles, and the run is not reported as clean")
        return 1'''
assert old2 in t
t = t.replace(old2, new2, 1)
p.write_text(t)
print("patched")
