import pathlib
p = pathlib.Path(".github/workflows/mcp-bundle.yml")
t = p.read_text()
old = "      - name: Publish both bundles on the release\n"
new = """      - name: Refuse to publish a bundle the registry entry does not pin
        run: |
          set -eu
          VERSION="${GITHUB_REF_NAME#v}"
          # Each registry entry records a fileSha256 for one URL. If a tag ever
          # moves ahead of those entries, the built bundle hashes to something
          # else, and publishing it would leave the entries pointing at bytes
          # that no longer match - installable-looking and unverifiable. The
          # entries and the tag move together, or not at all.
          for stem in claimgate claimgate-kit; do
            case "$stem" in
              claimgate) src=mcp ;;
              *)         src=mcp-kit ;;
            esac
            built="dist/$stem-$VERSION.mcpb"
            pinned="$(python3 scripts/pinned_hash.py "$src/server.json")"
            actual="$(sha256sum "$built" | cut -d' ' -f1)"
            if [ "$pinned" != "$actual" ]; then
              echo "$src/server.json pins $pinned but $built hashes to $actual" >&2
              echo "update $src/server.json, then re-tag" >&2
              exit 1
            fi
            echo "$stem: the registry entry's pinned hash matches the built bundle"
          done
      - name: Publish both bundles on the release
"""
assert old in t
p.write_text(t.replace(old, new, 1))
print("workflow patched")
