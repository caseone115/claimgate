import pathlib
p = pathlib.Path("scripts/check_mcpb_artifact.py")
t = p.read_text()

old = '''    via_uv = ["uv", "run", "--with", "mcp", "--python", python_exe, "python"]
    if works(via_uv):
        return via_uv + [str(suite), "--python", python_exe, "--server",
                         str(server)]'''
new = '''    # NOTE: no --python is passed on this path. The suite hands its own
    # interpreter to the server it spawns, so pointing the suite at the
    # mcp-less interpreter would leave the CLIENT able to import the SDK and the
    # SERVER unable to - which is a "Connection closed" from the server's own
    # ImportError, and is exactly the false red this file saw on the v0.1.0 run.
    # Letting the suite default to the interpreter uv resolved keeps both ends
    # on the same environment.
    via_uv = ["uv", "run", "--with", "mcp", "python"]
    if works(via_uv):
        return via_uv + [str(suite), "--server", str(server)]'''
assert old in t
p.write_text(t.replace(old, new, 1))
print("patched")
