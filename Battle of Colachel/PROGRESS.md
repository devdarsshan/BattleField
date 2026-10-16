# Battle of Colachel: production tracker

**Read this first if you are an AI agent (Claude, Gemini or any other) picking up this work.**
Then read `../CLAUDE.md` (channel rules and the Blender pipeline) and `../_channel-context/*.md`.
Update this file whenever you finish, start or change a beat. Keep it the single source of truth.

Last updated: 2026-10-16 (Claude: S12 canopy fix, S19-S28 voices, S19-S28 Flow references)

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
Flow references: `frames/flow_refs/`, named after the shot-list clip. Older beats kept both options (`Kxx_v1/v2.jpeg`, the
chosen one is named in the table); from S19 on only the selected image is saved (`Kxx.jpeg`). **Note:** the Flow
images sometimes paint the sea with wave lines; ignore that, the sea is always the faceted low-poly sea.

| Beat | Clip(s) | Content | Blender file / scripts | Status |
|---|---|---|---|---|
| S01-S04 | 01-07 | Dawn beach, stockade, Travancore camp, king, Dutch ships | `Colachel.blend` / `film.py`, `colachel_world.py` | ✅ Approved (1080p done, Charon voice) |
| S05-S06 | 05-07 | Monsoon, rice in stockade, gun fires, crane up | same | ✅ Approved (up to 1:36 of the review) |
| S07 | 08 | Cloud dissolve into the 3D map of Kerala | `Map.blend` / `map_film.py`, `map_world.py` | ✅ Approved (v4) |
| S08 | 09-10 | Map glide north to the Vembanad backwaters | same | ✅ Sent for review |
| S09 | 11-12 | Pepper hills, vines, baskets, river jetty + ship | `Pepper.blend` / `pepper_film.py`, `pepper_world.py` | ✅ Sent for review (`clip11-12_S09_review_720p.mp4`) |
| S10 | 13 | Map: kingdom forts pop up along the coast | `Map.blend` | ✅ Sent for review |
| S11 | 14-15 | Map: push in on Kochi, Dutch star fort turns orange | `Map.blend` | ✅ Sent for review |
| S12 | 16-17 | Kochi fort courtyard: Dutch + rajas sign contracts, porters to ship (ref K16_v1) | `Kochi.blend` / `kochi_film.py`, `kochi_world.py` | ⚠ Canopy pass fixed 2026-10-16 (camera keys 215-300 moved north and up so the canopy roof no longer fills the frame). **Re-render frames 147-368 only** (`--range 147 368`, delete those PNGs first), then re-encode the review |
| S13 | 18 | Map: glide south to Travancore's red fort | `Map.blend` | ✅ Rendered (`clip18_S13_review_720p.mp4` ready) |
| S14 | 19 | Padmanabhapuram palace town, young king on veranda (refs K19a_v1, K19b_v2) | `Palace.blend` / `palace_film.py`, `palace_world.py` | ✅ Rendered (`clip19_S14_review_720p.mp4` ready) |
| S15 | 20 | Palace courtyard: disloyal nobles led away, king alone (refs K20_v1/v2) | `Palace15.blend` / `palace15_film.py` | ✅ Rendered (`clip20_S15_review_720p.mp4` ready) |
| S16 | 21-22 | Map: red Travancore territory spreads north | `Map.blend` | ✅ Rendered (`clip21-22_S16_review_720p.mp4` ready) |
| S17 | 23 | English port: pepper onto red-flag English ship, Dutch ship leaves (refs K23_v1/v2) | `Port.blend` / `port_film.py`, `port_world.py` | ✅ Rendered (`clip23_S17_review_720p.mp4` ready) |
| S18 | 24 | Map: wide, big red Travancore vs small orange Kochi | `Map.blend` | ✅ Rendered (`clip24_S18_review_720p.mp4` ready) |
| S19 | 25 | Map: glide over the sea to Ceylon; a Dutch ship sails from it toward Kochi. Voice recorded (12.7 s) | ref **K25** · extend `map_world.py`/`map_film.py`: Ceylon is OUTSIDE `MAP_REGION` (it spans ~lat 6-10, lon 79.7-82); add the island and widen the region/sea | ⬜ Ready to build |
| S20 | 26 | Van Imhoff writing by candle in his study in Kochi fort, night. Voice 12.4 s | ref **K26** · new interior set (reuse Kochi fort look for the window view) | ⬜ Ready to build |
| S21 | 27 | Meeting under a canopy: king seated, Imhoff points firmly; Nair guards, Dutch soldiers. Voice 12.9 s | ref **K27** · new meeting set (can reuse `kit.make_canopy`, figures, palace roofs from `palace_world.py`) | ⬜ Ready to build |
| S22 | 28-29 | Same meeting: slow orbit; the king calm, gestures to the forests; Imhoff stiff. Voice 23.9 s (Koshy story) | ref **K27** (same set as S21) | ⬜ Ready to build |
| S23 | 30 | Close on the king, calm, arms folded. Voice 11.4 s | ref **K30** (same set) | ⬜ Ready to build |
| S24 | 31 | Map: orange war banner rises over Kochi, a column marches south. Voice 15.2 s | ref **K31** · `map_film.py` (Dutch star fort already there) | ⬜ Ready to build |
| S25 | 32 | Battle near Kollam: Dutch + allied lines advance on Travancore lines, powder store behind. Voice 12.0 s | ref **K32** · new battlefield set (paddy fields, earth banks) | ⬜ Ready to build |
| S26 | 33 | Shell hits the powder store, explosion, soldiers run, 16 cannons left. Voice 14.1 s | ref **K33** (same battlefield set) | ⬜ Ready to build |
| S27 | 34 | Varkala cliffs: a wall of ~5,000 Nairs stops the allies, who turn back. Voice 18.0 s | ref **K34** · new cliff set (red laterite cliffs, beach, faceted sea) | ⬜ Ready to build |
| S28 | 35 | Map: armies push back and forth around Kollam. Voice 8.1 s | ref **K35** · `map_film.py` (reuse territory tint and borders) | ⬜ Ready to build |
| S29-S69 | 36-82 | Ceylon reinforcements, landing at Colachel, siege, surrender, aftermath | — | ⬜ Not started (no voice, no refs) |

Sent to the user so far: S01-S04 (1080p), S07 (clip08 v4), S08, S09, S10, S11. S12-S18 reviews live on the E-drive machine (renders are not in git).
**Complete through S18:** S12, S13, S14, S15, S16, S17, S18 all rendered and encoded in `blender/renders/`.

**Next (Blender, on the E-drive machine):** (1) re-render S12 frames 147-368 and re-encode its review; (2) build
S19-S28 in order, following `_channel-context/Blender_Build_Rules.md`, each against its selected reference in the
table; voices for these beats are real Algieba recordings, so clip lengths are final.
**Next (Claude, this machine):** each day record the next 10 voices (S29-S38 next) and make their Flow references.

### Next beats (S19 onward) — what the shot list asks for
S19 map glide over the sea to Ceylon, a Dutch ship sails to Kochi · S20 van Imhoff at a desk by candle in Kochi fort ·
S21-S23 van Imhoff and Marthanda Varma meet under a canopy (keyframe K06 in `frames/`) · S24 map, Dutch war banner at
Kochi, soldiers march south · S25-S26 battle near Kollam, powder-store explosion (K07) · S27 Varkala cliffs ·
S28-S29 map · S30-S32 Dutch fleet off Colachel, landing, De Lannoy (K08) … see `Colachel_Shot_List.md` for the rest.
Old Flow keyframes K01-K15 in `frames/` are the original look targets; make fresh `flow_refs` for each beat anyway.

## 2b. Narration status

- **S01-S04:** old Charon recordings. **S05-S18:** temporary Windows voice. **Decided 2026-10-16: leave these as they
  are for now; re-record them in Algieba at the very end**, then re-time and re-render those beats.
- **S19-S28:** recorded in Algieba on 2026-10-16 (`audio/S19.wav` ... `S28.wav`). Clips for these beats take their
  length from the real recording automatically.
- **S29 onward:** not recorded. Free quota is 10 lines a day: record the next 10 each day with
  `python _tools/tts.py "Battle of Colachel/audio/Sxx.wav" "<line from lines.txt>" --voice Algieba`
  (wait ~25 s between lines). `audio/lines.txt` is filled to S30.

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
