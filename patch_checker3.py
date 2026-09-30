import pathlib
p = pathlib.Path("scripts/check_mcpb_artifact.py")
t = p.read_text()
old = '''    named = _server_json_filename(src) if True else None'''
new = old
oldblock = '''    named = _server_json_filename(src)
    if named and (ROOT / "dist" / named).is_file():
        return ROOT / "dist" / named
    pattern = VERSIONED.get(stem) or re.compile(
        rf"^{re.escape(stem)}-\\d+\\.\\d+\\.\\d+\\.mcpb$")
    found = sorted((p for p in (ROOT / "dist").glob("*.mcpb")
                    if pattern.match(p.name)),
                   key=lambda p: p.stat().st_mtime)
    return found[-1] if found else None'''
newblock = '''    named = _server_json_filename(src)
    if named:
        # The entry names a file. If that file is not on disk the answer is
        # NOT "some other bundle will do" - that would mean checking an
        # artifact the registry is not going to serve and reporting it green.
        path = ROOT / "dist" / named
        return path if path.is_file() else None
    pattern = VERSIONED.get(stem) or re.compile(
        rf"^{re.escape(stem)}-\\d+\\.\\d+\\.\\d+\\.mcpb$")
    found = sorted((p for p in (ROOT / "dist").glob("*.mcpb")
                    if pattern.match(p.name)),
                   key=lambda p: p.stat().st_mtime)
    return found[-1] if found else None'''
assert oldblock in t
t = t.replace(oldblock, newblock, 1)
p.write_text(t)
print("patched")
