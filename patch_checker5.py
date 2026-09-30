import pathlib, re
p = pathlib.Path("scripts/check_mcpb_artifact.py")
t = p.read_text()
start = t.index("def _ensure_mcp(")
end = t.index("def check_variant(")
new = '''def _ensure_mcp(python_exe: str) -> bool:
    """Make the MCP SDK importable by python_exe, or say it cannot be.

    The stdio suites import ``mcp.client``. This bit the v0.1.0 release run: the
    workflow step ran under ``uv run --with jsonschema``, so that environment had
    no ``mcp`` in it, and both packed servers reported "the packed server passes
    its own stdio suite: FAIL" with ModuleNotFoundError underneath. That was a
    dependency missing from the CHECK, not a fault in either bundle - and a
    check that reports the wrong thing is worse than no check. So the checker
    provides what it needs and, if it still cannot, says plainly that the run is
    a fault in the check rather than reporting the bundles clean.
    """
    def can_import() -> bool:
        return subprocess.run([python_exe, "-c", "import mcp"],
                              capture_output=True, text=True).returncode == 0

    if can_import():
        return True
    print("  ... the MCP SDK is not in this environment; installing it for the "
          "stdio suites")
    subprocess.run([python_exe, "-m", "pip", "install", "--quiet", "mcp"],
                   capture_output=True, text=True)
    return can_import()


'''
p.write_text(t[:start] + new + t[end:])
print("rewritten")
