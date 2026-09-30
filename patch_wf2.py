import pathlib
p = pathlib.Path(".github/workflows/mcp-bundle.yml")
t = p.read_text()
old = """      - name: Check the PACKED bundles, not the source they came from
        run: |
          set -eu
          uv run --with jsonschema --python 3.12 python scripts/check_mcpb_artifact.py
"""
new = """      - name: Check the PACKED bundles, not the source they came from
        run: |
          set -eu
          # Only jsonschema is requested here on purpose. The checker provides
          # its own MCP SDK for the stdio suites, because the first version of
          # this step ran under an environment without `mcp` and reported both
          # bundles as failing - a dependency missing from the CHECK, reported
          # as a fault in the artifact. Running it this way keeps that honest.
          uv run --with jsonschema --python 3.12 python scripts/check_mcpb_artifact.py
          uv run --with jsonschema --python 3.12 python scripts/test_check_mcpb_artifact.py
          uv run --with jsonschema --python 3.12 python scripts/check_mcpb_artifact.py --fixtures
"""
assert old in t
p.write_text(t.replace(old, new, 1))
print("workflow patched")
