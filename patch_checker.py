import pathlib
p = pathlib.Path("scripts/check_mcpb_artifact.py")
t = p.read_text()

old_variants = '''VARIANTS = [
    {"name": "claimgate", "artifact": "dist/claimgate-0.1.0.mcpb",
     "suite": "scripts/test_mcp_server.py"},
    {"name": "claimgate-kit", "artifact": "dist/claimgate-kit-0.1.0.mcpb",
     "suite": "scripts/test_mcp_kit_server.py"},
]'''
new_variants = '''# The artifact is discovered, not named. The bundle's version is stamped from
# the git tag, so a check that hard-codes "0.1.0" passes on this box and fails
# on the next release - which is exactly what happened on the v0.1.1 run, where
# both bundles existed under a different name and the checker called them both
# missing. Globbing also means a stale bundle from an earlier version cannot be
# silently checked in place of the one that was just built.
VARIANTS = [
    {"name": "claimgate", "stem": "claimgate",
     "suite": "scripts/test_mcp_server.py"},
    {"name": "claimgate-kit", "stem": "claimgate-kit",
     "suite": "scripts/test_mcp_kit_server.py"},
]


def find_artifact(stem: str) -> pathlib.Path | None:
    """The newest dist/<stem>-<version>.mcpb, or None."""
    found = sorted((ROOT / "dist").glob(f"{stem}-*.mcpb"),
                   key=lambda p: p.stat().st_mtime)
    return found[-1] if found else None'''
assert old_variants in t
t = t.replace(old_variants, new_variants, 1)

old_head = '''    arch = ROOT / v["artifact"]
    print(f"\\n--- {v['name']}  ({v['artifact']}) ---")
    ok(f"{v['name']}: the packed artifact exists", arch.is_file())
    if not arch.is_file():
        return'''
new_head = '''    arch = find_artifact(v["stem"])
    print(f"\\n--- {v['name']}  ({arch.name if arch else 'NOT FOUND'}) ---")
    ok(f"{v['name']}: a packed artifact exists in dist/", arch is not None)
    if arch is None:
        return'''
assert old_head in t
t = t.replace(old_head, new_head, 1)

old_rebuild = '''    if a.rebuild:
        for v in VARIANTS:
            subprocess.run([sys.executable,
                            str(ROOT / "scripts" / "mcp_bundle.py"), v["name"]],
                           check=True, cwd=ROOT)'''
new_rebuild = '''    if a.rebuild:
        for v in VARIANTS:
            subprocess.run([sys.executable,
                            str(ROOT / "scripts" / "mcp_bundle.py"), v["stem"]],
                           check=True, cwd=ROOT)'''
assert old_rebuild in t
t = t.replace(old_rebuild, new_rebuild, 1)

t = t.replace(
    '    extract = workdir / v["name"]',
    '    extract = workdir / v["name"]', 1)

p.write_text(t)
print("patched")
