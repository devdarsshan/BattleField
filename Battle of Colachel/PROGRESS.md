# Battle of Colachel: production tracker

**Read this first if you are an AI agent (Claude, Gemini or any other) picking up this work.**
Then read `../CLAUDE.md` (channel rules and the Blender pipeline) and `../_channel-context/*.md`.
Update this file whenever you finish, start or change a beat. Keep it the single source of truth.

Last updated: 2026-10-15, session paused at 80% of the Claude 5-hour limit (resets ~19:10 UTC)

---

## 1. How the film is made (decided with the user)

- **Blender 5.2 (EEVEE) builds every clip**, driven by Python scripts in `blender/`. Google Flow is only used to make
  **free reference images** (Nano Banana 2, 0 credits) before each clip is built. No Flow video credits are spent.
- **Per beat:** Flow reference stills (2 variants) → pick/approve → build in Blender to match them closely →
  check stills side by side with the reference → 720p review render with narration → send to the user →
  fix feedback → later a final 1080p render.
- **Quality bar is high.** The user rejected sparse or plain results more than once: "the more the detail the better".
  Match the Flow references in composition, density (plants, props), colours and detail. Colours must match the
  earlier beach clips (kit palette; AgX "Medium Low Contrast" / "Base Contrast").
- **Cuts:** a continuous camera within a location; a clean cut or a cloud dissolve is fine for a big change of place
  (beach → map, map → a close scene).
- **No text** in any image or render. Flags are plain colours.
- **Work order:** keep building beat after beat without pausing, several in parallel is fine, but **deliver reviews
  to the user in story order** (S09 before S10, even if S10 renders first).
- **Usage limit (Claude):** at ~75% of the 5-hour plan limit, finish what is running and ask the user before
  starting the next clip.
- **Narration:** real voice is Google Gemini TTS. Chosen voice: **Algieba** (current recordings S01-S04 are the older
  Charon voice). Free tier = only 10 requests/day, so beats without a recording use an estimated length and a
  temporary Windows voice (`blender/make_placeholders.py`). Recording the real take later re-times the clip.
  Never paste the API key anywhere; it lives in `~/.flow-mcp/gemini-key`. `_tools/tts.py` uses it.

## 2. Beat status

Script: `Colachel_Script.md` has 69 beats (S01-S69). Shot list: `Colachel_Shot_List.md` (82 clips).
Narration text per beat: `audio/lines.txt` (`Sxx|text`), currently filled to S18.
Flow references: `frames/flow_refs/` (`Kxx_v1/v2.jpeg`, named after the shot-list clip).

| Beat | Clip(s) | Content | Blender file / scripts | Status |
|---|---|---|---|---|
| S01-S04 | 01-07 | Dawn beach, stockade, Travancore camp, king, Dutch ships | `Colachel.blend` / `film.py`, `colachel_world.py` | ✅ Approved (1080p done, Charon voice) |
| S05-S06 | 05-07 | Monsoon, rice in stockade, gun fires, crane up | same | ✅ Approved (up to 1:36 of the review) |
| S07 | 08 | Cloud dissolve into the 3D map of Kerala | `Map.blend` / `map_film.py`, `map_world.py` | ✅ Approved (v4) |
| S08 | 09-10 | Map glide north to the Vembanad backwaters | same | ✅ Sent for review |
| S09 | 11-12 | Pepper hills, vines, baskets, river jetty + ship | `Pepper.blend` / `pepper_film.py`, `pepper_world.py` | ✅ Sent for review (`clip11-12_S09_review_720p.mp4`) |
| S10 | 13 | Map: kingdom forts pop up along the coast | `Map.blend` | ✅ Sent for review |
| S11 | 14-15 | Map: push in on Kochi, Dutch star fort turns orange | `Map.blend` | ✅ Sent for review |
| S12 | 16-17 | Kochi fort courtyard: Dutch + rajas sign contracts, porters to ship (ref K16_v1) | `Kochi.blend` / `kochi_film.py`, `kochi_world.py` | ⏸ PAUSED mid-build: world rebuilt for a smaller courtyard; still to do: re-place props, escorts, clerk, porter loop and camera keys, then stills vs K16_v1, 720p render, review mp4 |
| S13 | 18 | Map: glide south to Travancore's red fort | `Map.blend` | ✅ Rendered, review not sent yet |
| S14 | 19 | Padmanabhapuram palace town, young king on veranda (refs K19a_v1, K19b_v2) | `Palace.blend` / `palace_film.py`, `palace_world.py` | ⏸ PAUSED: builds cleanly (~40 s); next step was test stills at the K19a/K19b camera keys, compare, fix, then 720p render and review mp4 |
| S15 | 20 | Palace courtyard: disloyal nobles led away, king alone (refs K20_v1/v2) | planned `palace15_film.py` reusing `palace_world.py` | ⬜ Not started (refs ready) |
| S16 | 21-22 | Map: red Travancore territory spreads north | `Map.blend` | ✅ Rendered, review `clip21-22_S16_review_720p.mp4` ready (held for order) |
| S17 | 23 | English port: pepper onto red-flag English ship, Dutch ship leaves (refs K23_v1/v2) | `port_world.py`, `port_film.py` (no `Port.blend` yet) | ⏸ PAUSED: world script written, film script was being written; next: finish `port_film.py`, build, stills vs K23_v2, render, review mp4 |
| S18 | 24 | Map: wide, big red Travancore vs small orange Kochi | `Map.blend` | ✅ Rendered, review `clip24_S18_review_720p.mp4` ready (held for order) |
| S19-S69 | 25-82 | Van Imhoff, the threat, war, landing, siege, surrender, aftermath | — | ⬜ Not started |

Sent to the user so far: `Colachel_clips01-04_1080p.mp4`, `clip08_review_v4_720p.mp4`, `clip09-10_S08_review_720p.mp4`.
**Next to send, in order:** S12, S13, S14, S15, S16, S17, S18.
Ready but held for order (in `blender/renders/`): `clip18_S13_review_720p.mp4` (after S12),
`clip21-22_S16_review_720p.mp4` (after S14, S15), `clip24_S18_review_720p.mp4` (after S17).

**To resume:** all renders are finished and S09-S11 are sent. (1) Finish S12, S14 (+S15), S17 builds as described in the table; (2) send the reviews in order S12, S13, S14, S15, S16, S17, S18; (3) then S19 onward.
Encode one beat's review (map example, S16):
`ffmpeg -framerate 24 -start_number <first> -i frames_map_720p/f_%04d.png -i ../../audio/placeholder/S16.wav -filter_complex "[0:v]trim=end_frame=<n>,setpts=PTS-STARTPTS,format=yuv420p[v];[1:a]adelay=800|800,apad[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -c:a aac -shortest clip21-22_S16_review_720p.mp4`

### Next beats (S19 onward) — what the shot list asks for
S19 map glide over the sea to Ceylon, a Dutch ship sails to Kochi · S20 van Imhoff at a desk by candle in Kochi fort ·
S21-S23 van Imhoff and Marthanda Varma meet under a canopy (keyframe K06 in `frames/`) · S24 map, Dutch war banner at
Kochi, soldiers march south · S25-S26 battle near Kollam, powder-store explosion (K07) · S27 Varkala cliffs ·
S28-S29 map · S30-S32 Dutch fleet off Colachel, landing, De Lannoy (K08) … see `Colachel_Shot_List.md` for the rest.
Old Flow keyframes K01-K15 in `frames/` are the original look targets; make fresh `flow_refs` for each beat anyway.

## 3. Files and commands (Windows, Git Bash)

```
Battle of Colachel/
  PROGRESS.md                this tracker
  Colachel_Script.md         narration with [Sxx] beats
  Colachel_Shot_List.md      clip table
  Sources.md                 sources and disputed points
  frames/                    old Flow keyframes K01-K15; flow_refs/ = per-beat Flow references
  clips/                     the three old Flow video clips (look reference only)
  audio/                     S01-S04.wav (Charon), lines.txt, placeholder/ (temporary voices)
  blender/
    colachel_kit.py          shared low-poly assets: huts, palms, trees, boats, jetty, props, stockade,
                             tents, canopy, ships, cannon, clouds, rain, figures (villager, dutch, nair,
                             nair_spear, commander, king; stand/sit; walkers with walk cycles)
    colachel_world.py        beach diorama + weather + render settings (setup_render)
    film.py                  beach film S01-S06 (DESIGN_CLIPS, CAM_KEYS, WEATHER)
    kerala_geo.py            real Kerala coast/Ghats/rivers (50 m per km, Colachel at 0,0)
    map_world.py             3D map world (faceted sea, terrain, palms, rivers, lagoons, kingdom forts,
                             Dutch star fort, territory tint, borders)
    map_film.py              map segment S07, S08, S10, S11, S13, S16, S18 (one timeline, cut cameras)
    pepper_*, kochi_*, palace_*, port_*   one world + film script per close-up scene
    render_cli.py            background renderer (stills / frames / video)
    make_placeholders.py     temporary voice for unrecorded beats
    make_video.py            frames + narration -> mp4 (beach film)
    renders/                 frames_*/, *_review_720p.mp4, timing*.json
```

Blender: `"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"`

- Build a segment (headless): `blender -b -P map_film.py` → writes `Map.blend` and `renders/timing_map.json`
- Test stills: `blender -b Map.blend --python-expr "import bpy; bpy.context.scene.eevee.taa_render_samples=16" -P render_cli.py -- stills "<ABS WINDOWS PATH>\renders\x" 100 200 --res 960x540`
- Frames (resumable, skips existing): `... -P render_cli.py -- frames "<ABS PATH>\renders\frames_map_720p" --res 1280x720` with 24 samples for reviews, 32 at 1920x1080 for finals.
- Temporary voice: `python make_placeholders.py renders/timing_map.json`
- One beat's review video: frames `first..last` from the timing json, placeholder wav delayed 0.8 s, ffmpeg libx264 crf 18.
- Output paths for render_cli must be absolute Windows paths (`$(cygpath -w "$PWD")\\renders\\...`).

Gotchas learned:
- Never use a world volume for haze in EEVEE (renders black); use the bounded haze box.
- If a render or agent is killed mid-frame, frames mode leaves an EMPTY placeholder PNG for that frame and later
  runs skip it. Before encoding, delete PNGs under 2 KB (`find frames_x -size -2k -name '*.png' -delete`) and re-run.
- Rendering uses the one Intel Arc integrated GPU: ~2 s/frame at 720p. Renders in parallel slow each other down.
- When a map beat is added, rebuild `Map.blend`, then re-render only the new frame range (frames mode skips
  existing files). If an earlier beat's look changes, delete that beat's frames first.
- Flow MCP needs the Flow Studio service (`cd ~/flow-mcp && npm run studio`, port 8787) and a Flow project open in
  its Chrome window. Images: model "Nano Banana 2", `max_credits: 0`, always end prompts with "no text, no letters,
  no labels, no watermark".

## 4. If you are not Claude Code

The Blender MCP and Flow MCP tools were set up for Claude Code. Without them you can still do everything from a
terminal: Blender runs headless with the commands above; Flow reference images can be made by hand in Flow
(flow.google.com, Nano Banana 2, free) and saved into `frames/flow_refs/`. Do not run two agents on the same beat or
the same `.blend` at the same time; claim a beat by marking it ⏳ with your agent name in the table first.
