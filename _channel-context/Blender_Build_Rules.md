# Blender build rules (for every agent: Claude, Gemini, anyone)

These are the rules the approved clips S01-S18 were built with. Follow them for every new beat so the film keeps one
look. If a rule conflicts with what the user asks, the user wins; write the new decision into `PROGRESS.md`.

## 0. The three things that matter most (the user has flagged all three)

### A. Same world, same parts, every scene: REUSE
The film must look like ONE world, not a set of unrelated scenes. Recent builds drifted: new scenes invented their own
palms, huts, figures, sea and colours. That is the most important thing to fix.
- **Before writing any geometry, list what already exists** (`grep -n "^def " *.py` in `blender/`) and use it.
  `colachel_kit.py` is the shared library: palms, trees, bushes, huts, boats, jetty, crates, barrels, sacks, fences,
  stockade, tents, canopy, ships, cannon, clouds, rain, and all figures (villager, dutch, nair, nair_spear,
  commander, king; stand/sit; walkers). Scene worlds (`pepper_world.py`, `kochi_world.py`, `palace_world.py`,
  `port_world.py`) and `map_world.py` hold the sets.
- **Import, never copy.** If you need a variant (a seated official, a young king, a porter with a sack), add it to
  `colachel_kit.py` as a parameter or a new function, so every later scene gets the same part.
- **Recurring characters must be identical everywhere:** Marthanda Varma, van Imhoff, De Lannoy, Dutch soldiers, Nair
  soldiers. Same figure function, same materials, same proportions. Define each named character ONCE in the kit.
- **Recurring places are the same set:** the Kochi fort (map star fort and the courtyard must agree: orange walls),
  Padmanabhapuram, Colachel beach and stockade, the 3D map. Load or import the existing set and extend it.
- **One palette, one light, one sea:** `kit.PALETTE` colours, the warm low sun + haze box from `colachel_world.py`,
  and the faceted sea (`make_sea` / `map_world.build_sea`). Never a new grade or a new water.
- If you find two versions of the same thing, merge them into the kit and update both scenes to use it.

### B. Detail
"The more the detail the better." Each frame should be as full as its Flow reference: rows of palms several deep,
clusters of props (crates, sacks, baskets, pots, barrels), fences, paths, stones, ground plants, smoke, flags, and
people doing things (walking, carrying, idling). Compare every test still side by side with the reference and
list what is missing before you call it done. Empty ground, flat walls and frozen figures are not acceptable.

### C. Plan first, then work in parallel
- **Plan the whole batch before building anything.** For the next beats (e.g. S19-S28) write a short plan in
  PROGRESS.md: which sets are new, which are reused, which new kit parts are needed (build those FIRST, once, so
  every scene shares them), the camera idea per beat, and the order of work.
- **Parallelise:** build the shared kit parts first; then independent scenes (different `.blend` files) can be built
  by separate agents at the same time, each owning its own `<scene>_world.py` / `<scene>_film.py`. Never two agents
  on the same file. Map beats all live in `map_film.py`: give them to one agent.
- **Keep the GPU busy:** while agents build and test the next scenes with small stills, run a render queue for the
  finished ones (PNG frames are resumable; one 720p render at a time is fastest on one GPU, two at once just share
  it). Queue renders back to back (a PowerShell/bash script) instead of waiting between them.

## 1. The loop for one beat (do not skip steps)

1. **Claim it.** In `Battle of Colachel/PROGRESS.md`, mark the beat ⏳ with your agent/device name.
2. **Read the inputs.** The beat's line in `audio/lines.txt`, its row(s) in `Colachel_Shot_List.md`, and the
   selected Flow reference(s) listed for it in PROGRESS.md (`frames/flow_refs/Kxx_*.jpeg`). If a beat has no
   approved reference yet, stop and ask; do not invent the look.
3. **Reuse before you build.** Check `colachel_kit.py` (assets and figures), `colachel_world.py` (beach),
   `map_world.py` (map), and the scene worlds (`pepper_world.py`, `kochi_world.py`, `palace_world.py`,
   `port_world.py`). Import their functions; never copy-paste a big block. A set that reappears later
   (Kochi fort, the palace, the beach, the map) must be the same set, extended, not rebuilt differently.
4. **Write two scripts:** `<scene>_world.py` (the set, assets) and `<scene>_film.py` (timing + camera), or add the
   beat to an existing film script if it happens in an existing set (e.g. all map beats go in `map_film.py`).
5. **Iterate with stills**, small and cheap: 960x540, 12-16 samples, 3-5 key frames. Put each still **side by side
   with its Flow reference** (`ffmpeg ... hstack`) and look at it. Fix the differences. Repeat until close.
   Typical fixes: more density (plants, props, people), stronger colour, camera framing, a missing prop.
6. **Render the review:** 1280x720, 24 samples, PNG frames (resumable) → mp4 with the narration 0.8 s in.
7. **Check before sending:** delete empty PNGs (< 2 KB, left by an interrupted render) and re-run frames; make sure
   no frame has the camera inside or right against an object (a roof, a wall, a palm) filling the shot.
8. **Update PROGRESS.md** (status, file names, frame range, anything unusual) and commit the scripts and `.blend`.

## 2. Look and style

- **Low-poly diorama:** flat-shaded, faceted, matte. Bevel small objects slightly (`kit.MB(bevel=0.01-0.03)`) so
  edges catch light. Figures are blocky with minimal faces (eyes, nose, moustache), as in `style-refs/`.
- **Detail density is the user's #1 complaint when missed.** "The more the detail the better." Fill scenes the way
  the Flow references are filled: rows of palms, clusters of props (crates, sacks, baskets, pots), fences, paths,
  people. Empty sand or flat green is wrong.
- **Colours:** use `kit.PALETTE` names (sand, grass, frond, thatch, plank, coat_blue, red, gold, ...). Greens and
  sand must match the beach clips; do not invent pale or neon variants. Travancore = red, Dutch = orange on the map
  (blue coats on figures), English = plain red flag ships, other kingdoms = their own colours.
- **Colour management:** AgX, look "AgX - Medium Low Contrast" (beach) or "AgX - Base Contrast" (map, close scenes).
  Exposure near 0.
- **Light:** warm low sun with long soft shadows, slight haze (the bounded haze box, never a world volume).
- **Sea:** always the faceted low-poly sea (jittered triangulated grid, vertex colours turquoise → blue, rolling
  Displace swell, flat near the shore). Never painted wave lines. Ships rock and bob on it.
- **No text anywhere.** Flags are plain colour. Parchment and contracts are blank.
- **Animate life:** idle sway on standing figures (`kit.animate_idle`), walkers (`kit.make_walker` +
  `kit.animate_walk`), ships rocking, smoke, flags. A frozen scene reads as a still.

## 3. Camera and timing

- One continuous move within a location; a clean cut or a cloud dissolve between places (beach → map → close
  scene). Map shots are straight top-down, north up.
- Clip length comes from the narration (`audio/Sxx.wav` if it exists, else the text estimate) plus 0.8 s lead and
  0.6 s tail, minimum 10 s. Use the `timed_clips()` / `retime()` pattern from `film.py` / `map_film.py`, and write
  camera keys in design frames so a later voice re-record re-times them automatically.
- Time visual events to the words: when the line names a place, a fort or an action, that is when it happens
  on screen.
- Keep the camera out of objects: when it passes a roof, wall or tree, route around it or rise above it.

## 4. Facts

- Everything shown must match the script and `Sources.md`. Do not add events, numbers or flags the script does not
  support. If the reference image shows something unhistorical, leave it out.

## 5. Machine notes

- Blender 5.2, EEVEE. Run headless: `blender -b -P <scene>_film.py`, then `render_cli.py` (see PROGRESS.md for the
  exact commands). Output paths for render_cli must be absolute.
- Scripts find their own folder (`HERE = os.path.dirname(os.path.abspath(__file__))`); never hard-code a drive.
- Rendered frames and mp4s are not in git (`.gitignore`). Commit scripts, `.blend` files, references and audio.
