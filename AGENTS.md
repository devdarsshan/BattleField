# Instructions for AI agents (Gemini, Claude, any other)

This folder is a YouTube channel on battle history. Before doing anything, read in this order:

1. `Battle of Colachel/PROGRESS.md` — live status, decisions, which beat is next, its selected Flow references.
2. `_channel-context/Blender_Build_Rules.md` — the design and build rules every Blender clip must follow.
3. `CLAUDE.md` — channel rules and the Blender pipeline (they apply to every agent, not just Claude).

Update `PROGRESS.md` when you start (claim the beat) and when you finish a beat.

**Most important (from the user):** keep every scene in the same structure by REUSING the shared components in
`blender/colachel_kit.py` and the existing sets (never rebuild a palm, hut, figure, sea or a recurring place
differently); make scenes as detailed as their Flow references; plan the whole batch first, then build in parallel
and keep the GPU rendering. Details in `_channel-context/Blender_Build_Rules.md`, section 0.
