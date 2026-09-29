# This is the policy file. ClaimGate reads it and enforces it on every draft.

Every rule below is a claim this organisation is not allowed to publish, or is
only allowed to publish with evidence attached. Edit it: delete what does not
apply to you, add what does. The rules you write are the ones that get enforced
— the tool has no opinion of its own.

categories
    prohibited  the draft is blocked. Nothing publishing on a deadline without
                someone removing it.
    restricted  flagged, and blocks unless the draft carries the evidence the
                rule asks for.
    style       reported, never blocks.

severity
    high        treated as blocking for a prohibited or restricted rule.
    medium      reported; blocks only under --strict.
