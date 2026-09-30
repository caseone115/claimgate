import pathlib
p = pathlib.Path("scripts/check_mcpb_artifact.py")
t = p.read_text()

old = '''def find_artifact(stem: str) -> pathlib.Path | None:
    """The newest dist/<stem>-<version>.mcpb, or None."""
    found = sorted((ROOT / "dist").glob(f"{stem}-*.mcpb"),
                   key=lambda p: p.stat().st_mtime)
    return found[-1] if found else None'''
new = '''# A plain glob on "claimgate-*" also matches "claimgate-kit-*", which would let
# the engine check the kit's bundle and call it its own. So the artifact is
# resolved from the registry entry that will serve it - server.json's package
# identifier is the URL the registry fetches, and the file it names is the file
# that must exist. A version-number regex is the fallback for a checkout where
# server.json is absent, and "kit" is not a digit, so the two cannot collide.
VERSIONED = {}


def _server_json_filename(src: pathlib.Path) -> str | None:
    f = src / "server.json"
    if not f.is_file():
        return None
    try:
        data = json.loads(f.read_text())
    except (OSError, ValueError):
        return None
    for pkg in data.get("packages") or []:
        url = str(pkg.get("identifier", ""))
        if url.endswith(".mcpb"):
            return url.rsplit("/", 1)[-1]
    return None


def find_artifact(stem: str, src: pathlib.Path) -> pathlib.Path | None:
    """The dist bundle this variant's own registry entry points at, or None."""
    named = _server_json_filename(src)
    if named and (ROOT / "dist" / named).is_file():
        return ROOT / "dist" / named
    pattern = VERSIONED.get(stem) or re.compile(
        rf"^{re.escape(stem)}-\\d+\\.\\d+\\.\\d+\\.mcpb$")
    found = sorted((p for p in (ROOT / "dist").glob("*.mcpb")
                    if pattern.match(p.name)),
                   key=lambda p: p.stat().st_mtime)
    return found[-1] if found else None'''
assert old in t
t = t.replace(old, new, 1)

t = t.replace('''    {"name": "claimgate", "stem": "claimgate",
     "suite": "scripts/test_mcp_server.py"},
    {"name": "claimgate-kit", "stem": "claimgate-kit",
     "suite": "scripts/test_mcp_kit_server.py"},''',
'''    {"name": "claimgate", "stem": "claimgate", "src": "mcp",
     "suite": "scripts/test_mcp_server.py"},
    {"name": "claimgate-kit", "stem": "claimgate-kit", "src": "mcp-kit",
     "suite": "scripts/test_mcp_kit_server.py"},''', 1)

t = t.replace('    arch = find_artifact(v["stem"])',
              '    arch = find_artifact(v["stem"], ROOT / v["src"])', 1)
p.write_text(t)
print("patched")
