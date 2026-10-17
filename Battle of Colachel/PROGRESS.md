# Battle of Colachel: production tracker

**Read this first if you are an AI agent (Claude, Gemini or any other) picking up this work.**
Then read `../CLAUDE.md` (channel rules and the Blender pipeline) and `../_channel-context/*.md`.
Update this file whenever you finish, start or change a beat. Keep it the single source of truth.

Last updated: 2026-10-17 (Claude: S29 voice, lines S39-S48, Flow refs K48-K58, S39-S48 built in Blender)

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
| S12 | 16-17 | Kochi fort courtyard: Dutch + rajas sign contracts, porters to ship (ref K16_v1) | `Kochi.blend` / `kochi_film.py`, `kochi_world.py` | ✅ Approved |
| S13 | 18 | Map: glide south to Travancore's red fort | `Map.blend` | ✅ Approved |
| S14 | 19 | Padmanabhapuram palace town, young king on veranda (refs K19a_v1, K19b_v2) | `Palace.blend` / `palace_film.py`, `palace_world.py` | ✅ Approved |
| S15 | 20 | Palace courtyard: disloyal nobles led away, king alone (refs K20_v1/v2) | `Palace15.blend` / `palace15_film.py` | ✅ Approved |
| S16 | 21-22 | Map: red Travancore territory spreads north | `Map.blend` | ✅ Approved |
| S17 | 23 | English port: pepper onto red-flag English ship, Dutch ship leaves (refs K23_v1/v2) | `Port.blend` / `port_film.py`, `port_world.py` | ✅ Approved |
| S18 | 24 | Map: wide, big red Travancore vs small orange Kochi | `Map.blend` | ✅ Approved |
| S19 | 25 | Map: Ceylon (real outline), Dutch ship sails to India | `Map.blend` · ref **K25** | ✅ REBUILT. Map frames 2118-2456 (delete old PNGs >= 2118 first) |
| S20 | 26 | Van Imhoff writing by candle in his study in Kochi fort, night | `Study.blend` / `study_film.py`, `study_world.py` · ref **K26** | ✅ REBUILT 2026-10-16 (v1 rejected). Frames 1-331 (real voice). Render on GPU machine |
| S21 | 27 | Meeting: king on throne, Imhoff points, guards | `Meeting.blend` / `meeting_film.py`, `meeting_world.py` · ref **K27** | ✅ REBUILT. Frames 1-343 |
| S22 | 28-29 | Same meeting, orbit, the Koshy story | `Meeting.blend` · ref **K27** | ✅ REBUILT. Frames 344-950 |
| S23 | 30 | Close on the king, arms folded | `Meeting.blend` · ref **K30** | ✅ REBUILT. Frames 951-1258 |
| S24 | 31 | Map: war banner over Kochi, column marches south | `Map.blend` · ref **K31** | ✅ REBUILT. Map frames 2457-2854 |
| S25 | 32 | Battle near Kollam | `Battle.blend` / `battle_film.py`, `battle_world.py` · ref **K32** | ✅ REBUILT. Frames 1-322 |
| S26 | 33 | Powder store explosion, 16 guns lost | `Battle.blend` · ref **K33** | ✅ REBUILT. Frames 323-695 |
| S27 | 34 | Varkala cliffs, the Nair wall | `Varkala.blend` / `varkala_film.py`, `varkala_world.py` · ref **K34** | ✅ REBUILT. Frames 1-465 |
| S28 | 35 | Map: armies push back and forth at the frontier | `Map.blend` · ref **K35** | ✅ REBUILT. Map frames 2855-3094 |
| S29 | 36 | Map: ship from Ceylon arrives at Kochi; dotted sea route south to the tip | `Map.blend` · ref **K36** | ✅ BUILT (device voice). Map frames 3095-3540. Map sea swell is now pinned (`SEA_SWELL_FRAMES`), so adding beats never shifts earlier frames |
| S30 | 37 | Warships fire broadsides at Colachel | `Landing.blend` / `landing_film.py`, `landing_world.py` · ref **K37** | ✅ BUILT, frames 1-456 (wash-out fixed: beat-only sun/haze/sea keys; sea facets could be crisper) |
| S31 | 38 | Seven ships, boats, soldiers wade ashore | `Landing.blend` · ref **K38** | ✅ BUILT, frames 457-799 (wash-out fixed) |
| S32 | 39 | De Lannoy on the beach, pointing | `Landing.blend` · ref **K39** | ✅ BUILT, frames 800-1192 (kit kind `delannoy`) |
| S33 | 40 | High view: beach → paddies → palace inland | `Inland.blend` / `inland_film.py`, `inland_world.py` · ref **K40** | ✅ BUILT, frames 1-408 (polish later: less haze, richer greens, palace bigger in frame) |
| S34 | 41 | Stockade rises post by post; column marches inland, villages burn | `Landing.blend` · ref **K41** | ✅ BUILT, frames 1193-1556 |
| S35 | 42-43 | Dutch column near Kottar, palace roofs behind | `Inland.blend` · ref **K42** | ✅ BUILT, frames 409-943 |
| S36 | 44-45 | Kalkulam fort, king on the elephant, ~2,400 Nairs | `Inland.blend` · ref **K44** | ✅ BUILT, frames 944-1255 (kit `make_elephant`) |
| S37 | 46 | Thiruvattar temple at dawn, sword laid down | `Inland.blend` · ref **K46** | ✅ BUILT, frames 1256-1696 (polish later: more pink-gold dawn, richer gopuram carving) |
| S38 | 47 | Monsoon on the beach | `Landing.blend` · S05 storm | ✅ BUILT, frames 1557-1997 (rain could be heavier) |
| S39 | 48 | Map: stormy Gulf of Mannar, Dutch ship turns back (built by a helper agent) | `Map.blend` / `map_film.py`, `map_world.py` (`build_s39`) · ref **K48** | ✅ BUILT (device voice), map frames 3535-3886. Camera is only 38 deg off top-down, so the ship reads from above; clouds/rain heavier than K48; ship shadow hard |
| S40 | 49 | Travancore column drives the Dutch down the track to the stockade | `Siege.blend` / `siege_film.py`, `siege_world.py` · ref **K49** | ✅ BUILT (device voice), frames 1-266 |
| S41-S42 | 50-51 | Siege ring round the stockade (soldier line, 2 rows of tents, fires), orbit to the fishing village | `Siege.blend` · refs **K50, K51** | ✅ BUILT, frames 267-864 (one shared camera) |
| S43 | 52 | Fishermen refuse the Dutch officer's bag of coins | `Siege.blend` · ref **K52** (re-made) | ✅ BUILT, frames 865-1343 |
| S44 | 53 | Fishermen push palm-trunk "cannons" on carts west along the beach | `Siege.blend` · ref **K53** | ✅ BUILT, frames 1344-1715 |
| S45 | 54 | Row of fake guns on the western dunes, two Dutch ships far out | `Siege.blend` · ref **K54** (re-made) | ✅ BUILT, frames 1716-1955 |
| S46 | 55-56 | Two ships come in, shore guns fire (x 84-100, east of the stockade), ships turn away | `Siege.blend` · refs **K55, K56** | ✅ BUILT, frames 1956-2208 |
| S47 | 57 | Inside the stockade in heavy rain, the last rice sacks counted | `Siege.blend` · ref **K57** | ✅ BUILT, frames 2209-2448 |
| S48 | 58 | Hillside battery fires at the stockade | `Siege.blend` · ref **K58** | ✅ BUILT, frames 2449-2701 (palms still crowd the foreground) |
| S49 | 59 | Glowing ball from the battery drops into the powder barrel (camera follows it) | `Surrender.blend` / `surrender_film.py`, `surrender_world.py` · ref **K59** | ✅ BUILT (device voice), frames 1-310 |
| S50 | 60-61 | Explosion, men thrown back, fire spreads, rice store burns (camera shared with S49) | `Surrender.blend` · ref **K60** | ✅ BUILT, frames 311-584 |
| S51 | 62-63 | Smoke drifts over the burnt stockade, dazed Dutch, Travancore ring outside | `Surrender.blend` · ref **K62** | ✅ BUILT, frames 585-873 |
| S52 | 64 | Dutch hoist a white flag over the smoking stockade | `Surrender.blend` · ref **K64** | ✅ BUILT, frames 874-1339 |
| S53 | 65 | Dutch officers, De Lannoy first, hand swords to Travancore commanders (beach east of the stockade) | `Surrender.blend` · ref **K65** | ✅ BUILT, frames 1340-1832 |
| S54 | 66 | Prisoners marched inland along the track, hill fort ahead | `Surrender.blend` · ref **K66** | ✅ BUILT, frames 1833-2072 (fort barely in frame; haze) |
| S55-S58 | 67-70 | Udayagiri: the king offers De Lannoy a job, he bows; drill ground; the sash | `Udayagiri.blend` / `udayagiri_film.py`, `udayagiri_world.py` (helper agent) · refs **K67-K70** | ✅ BUILT (device voice), frames 1-1141: S55 1-240, S56 241-480, S57 481-901, S58 902-1141. Weak: kit king is bare-chested (no red-gold robe), Nair has no red coat (K69 has red-coat muskets), S57 foreground empty, S56 bow stiff |
| S59-S69 | 71-82 | Map north, chapel, Mavelikkara treaty, temple, pillar today, sunset | - | ⬜ Not started (11 beats) |

**Complete and approved through S18:** S01–S18 all reviewed and approved.
**Beats S19–S28 built:** All 5 scene blend files (`Map.blend`, `Study.blend`, `Meeting.blend`, `Battle.blend`, `Varkala.blend`) fully built, visual stills verified against Flow references K25–K35.
- S19, S20, S21 review videos completed:
  - `renders/clip25_S19_review_720p.mp4` (14.1s, Ceylon + Dutch Galleon)
  - `renders/clip26_S20_review_720p.mp4` (13.8s, Van Imhoff Study by candle)
  - `renders/clip27_S21_review_720p.mp4` (14.3s, Grand Pavilion Meeting)
- Thermal Guard actively regulating hardware in `render_cli.py` & `pipeline_s19_to_s28.ps1` (250ms frame breather, active 76°C GPU throttle & 68°C cooldown, 20s inter-clip break). Zero crashes.

**Status 2026-10-17:** S01-S38 are all built (S29-S38 committed). S19-S28 render pipeline ran on the E-drive machine.
**Voices:** S29 recorded in Algieba today (`audio/S29.wav`). The Gemini free quota then said "10 per day, retry in ~18 h",
so S30-S38 are still device voice. `audio/lines.txt` is now filled to S48. Next quota window: record S30-S38 (9 lines),
then S39-S40.
**Flow references:** K48-K70 used for the built beats (S39-S58). K71-K82 made 2026-10-17 for S59-S68, awaiting approval: K71 S59 map north + Nedumkotta
wall, K73 S60 chapel and tomb, K74 S61 Dutch ships leave Kanyakumari, K75 S62 Mavelikkara treaty tent, K76 S63 map, Travancore biggest, pepper ships,
K77 S64 king lays down his sword at the temple, K78 S65 victory pillar today (also the set for S66), K80 S67 rise from the pillar over the sea,
K82 S68 sunset over the empty beach. S66/S69 (title/outro cards) need no ref.
**Render note:** S29's real voice changes its length, so the map beat S29 (frames 3095-3540) re-times; rebuild `Map.blend`
and delete map frames >= 3095 before rendering. Any other device must pull the latest commit first (audio wavs are tracked,
`renders/` is not).
**Next (Claude, this machine):** record S30-S38 voices, then Flow refs K71+; build S49+ in Siege.blend once K59-K70 are approved.

### Build plan for S29-S38 (plan first, then parallel, per Blender_Build_Rules.md section 0)
Shared parts to add to `colachel_kit.py` FIRST (once, before any scene uses them):
- figure kind `"delannoy"` (young officer: navy coat with gold trim, white cross-belts, orange sash, tricorn, sword,
  own dark hair) and a pointing pose; an **elephant** with a royal howdah (for S36); a **rowing boat full of soldiers**
  (instance figures into `make_boat`); **muzzle flash + smoke puff** helper (generalise `build_battery`'s shot) for ship
  broadsides; a **stockade build-up** helper (posts rise one by one; the `make_stockade` asset already exists).
Then three independent streams (separate files, can run in parallel on different agents):
1. **Beach stream** (one new film script, e.g. `landing_film.py`, reusing `colachel_world.py` + its weather):
   S30 broadside (K37) → S31 landing (K38) → S32 De Lannoy (K39) → S34 stockade going up + column inland (K41) →
   S38 monsoon (reuse the approved S05 storm settings). Same Colachel beach, village and stockade site as S01-S06.
2. **Inland stream** (reuse `palace_world.py` for every palace view): S33 high view beach→paddies→palace (K40),
   S35 Dutch column near Kottar with the palace roofs behind (K42), S36 Kalkulam fort + elephant + Nair crowd (K44,
   new fort set), S37 Thiruvattar temple at dawn (K46, new temple set).
3. **Map stream** (`map_film.py`, one agent only): S29 ship arrives at Kochi + dotted route to the tip (K36).
Each beat: stills vs its ref saved to `blender/renders/compare/`, then commit; renders happen on the GPU machine
(or Kaggle, see `_tools/kaggle/README.md`).

Decision 2026-10-16: from S19 on, map beats may use a slight camera tilt (10-38°, as in their Flow refs); forts
may be scaled down inside a beat when armies must read. Map frames 1-2117 (S07-S18) are unchanged.

### Next beats (S19 onward) — what the shot list asks for
S19 map glide over the sea to Ceylon, a Dutch ship sails to Kochi · S20 van Imhoff at a desk by candle in Kochi fort ·
S21-S23 van Imhoff and Marthanda Varma meet under a canopy (keyframe K06 in `frames/`) · S24 map, Dutch war banner at
Kochi, soldiers march south · S25-S26 battle near Kollam, powder-store explosion (K07) · S27 Varkala cliffs ·
S28-S29 map · S30-S32 Dutch fleet off Colachel, landing, De Lannoy (K08) … see `Colachel_Shot_List.md` for the rest.
Old Flow keyframes K01-K15 in `frames/` are the original look targets; make fresh `flow_refs` for each beat anyway.

## 2c. Production Plan: Beats S19–S28 (The Threat & The First Round)

*Planned 2026-10-16 (Gemini) following `Blender_Build_Rules.md` Section 0. Voices recorded in Algieba (`audio/S19.wav` ... `S28.wav`). Flow references selected in `frames/flow_refs/` (`K25.jpeg` ... `K35.jpeg`).*

### 1. Scene Grouping & Target Files
- **`Map.blend` (`map_film.py`, `map_world.py`)** — Map beats:
  - **S19 (Clip 25)**: Glide south-east over sea to Ceylon (~lat 6–10, lon 79.7–82) with Dutch star fort; Dutch East Indiaman sails north-west towards Kochi. Voice 12.7 s (341 frames). Ref: `K25.jpeg`. Extension: widen `MAP_REGION`, add Ceylon mesh with faceted hills, palm belt, beaches, Dutch star fort.
  - **S24 (Clip 31)**: Orange Dutch war banner hoists over Kochi star fort; column of Dutch/allied soldiers marches south toward Kollam. Voice 15.2 s (400 frames). Ref: `K31.jpeg`.
  - **S28 (Clip 35)**: Armies push back and forth around Kollam with animated arrows and smoke puffs; red Travancore vs orange Dutch spheres of control. Voice 8.1 s (230 frames). Ref: `K35.jpeg`.
- **`Study.blend` (`study_film.py`, `study_world.py`)** — Dutch Kochi fort interior:
  - **S20 (Clip 26)**: Night interior. Van Imhoff in powdered wig and dark coat writing by candlelight at desk (scrolls, quill, globe, bookcase, warm candle light, open window showing Kochi harbour at night with docked Dutch ship). Voice 12.4 s (332 frames). Ref: `K26.jpeg`.
- **`Meeting.blend` (`meeting_film.py`, `meeting_world.py`)** — Canopy meeting (continuous scene, 3 camera setups):
  - **S21 (Clip 27)**: Van Imhoff standing under royal canopy pointing firmly, backed by 2 Dutch musket guards; King Marthanda Varma seated on throne with Nair guards behind. Voice 12.9 s (344 frames). Ref: `K27.jpeg`.
  - **S22 (Clips 28-29)**: Slow orbit around treaty table; King calm, gestures toward forests; Imhoff stiff. Voice 23.9 s (608 frames). Ref: `K27.jpeg`.
  - **S23 (Clip 30)**: Tight close-up on the King, arms folded, calm and resolute. Voice 11.4 s (308 frames). Ref: `K30.jpeg`.
- **`Battle.blend` (`battle_film.py`, `battle_world.py`)** — Battlefield near Kollam (continuous scene):
  - **S25 (Clip 32)**: Dutch lines in blue coats and allied troops advance with cannons across diked green paddy fields towards Travancore earthworks with 16 cannons and Nair warriors. Voice 12.0 s (322 frames). Ref: `K32.jpeg`.
  - **S26 (Clip 33)**: Mortar shell arcs over, strikes thatch powder storehouse; low-poly explosion burst (fire shards, expanding grey smoke); barrels blast outward; Travancore troops retreat, leaving cannons. Voice 14.1 s (372 frames). Ref: `K33.jpeg`.
- **`Varkala.blend` (`varkala_film.py`, `varkala_world.py`)** — Varkala Cliffs stand-off:
  - **S27 (Clip 34)**: Red laterite cliffs rising over golden beach and faceted turquoise sea. Solid phalanx wall of 5,000 Nair warriors with shields and raised swords blocking cliff road. Approaching allied/Dutch army halts and turns back. Voice 18.0 s (466 frames). Ref: `K34.jpeg`.

### 2. Shared Kit Additions (`colachel_kit.py`)
Build once before scene construction so all scenes share identical components:
- `imhoff`: Dutch Governor figure with periwig (`wig`), dark frock coat (`dark`/`plank`), white jabot, white stockings, black buckled shoes. Poses: standing with pointing arm outstretched, seated writing pose with quill.
- `make_throne()`: Ornate royal wooden throne with red cushion, gold trim, and carved finials.
- `make_paddy_field()`: Rectangular diked plots with lush green rice paddies.
- `make_earthworks()`: Earthen rampart / redoubt trenches.
- `make_powder_store()`: Thatch-roofed wooden ammunition depot with barrels and crates.
- `make_explosion()`: Faceted low-poly fire shard and expanding smoke puff cluster.

### 3. Execution & Render Order
1. Implement shared kit additions in `colachel_kit.py`.
2. Build `Map.blend` (S19, S24, S28).
3. Build `Study.blend` (S20).
4. Build `Meeting.blend` (S21, S22, S23).
5. Build `Battle.blend` (S25, S26).
6. Build `Varkala.blend` (S27).
7. Test stills side-by-side with Flow refs → queue 720p renders & encode reviews in story order.

## 2b. Narration status

- **S01-S04:** old Charon recordings. **S05-S18:** temporary Windows voice. **Decided 2026-10-16: leave these as they
  are for now; re-record them in Algieba at the very end**, then re-time and re-render those beats.
- **S19-S28:** recorded in Algieba on 2026-10-16 (`audio/S19.wav` ... `S28.wav`). Clips for these beats take their
  length from the real recording automatically.
- **S29-S38:** DEVICE voice (`audio/placeholder/`, made by `blender/device_voice.py`); final Algieba later.
  See `audio/VOICES.md` for every beat's voice.
- **S39 onward:** not recorded. Free quota is 10 lines a day: record the next 10 each day with
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

## Siege beats S39-S48 (2026-10-17)
- New kit parts (`colachel_kit.py`, end of file): `make_log_cannon` + `animate_cart` (fake palm-trunk cannon on a cart), `make_coin_bag`, `make_fishing_net`.
- `landing_world.build_stockade(..., full=True)` gives the finished wall; `clear_around` also clears `BatteryPalm`.
- New: `siege_world.py`, `siege_film.py` (build: `blender -b -P siege_film.py`, writes `Siege.blend`, `renders/timing_siege.json`).
  Camera keys and events are fractions of each beat, so a later re-recorded voice re-times everything. S41+S42 share one camera.
- `compare_siege.py TAG f133:K49 ...` makes side-by-side stills against the Flow refs in `renders/compare/`.
- Device-voice placeholders made for S39-S48. Not rendered as video yet (only test stills). Polished 2026-10-17: S43 now filmed from the sea side
  (officer with bag at left, fishermen turning away), S46 guns recoil, S47 patchy mud and smaller tents, S48 steep top-down camera clear of palms,
  S40 pursuers and track cleared of palms. Still open: low-poly clouds are rarely in frame in beach beats; S47 tents are still plain white cones.
- S30-S38 are still the device voice (quota); S29 is Algieba.

## Surrender beats S49-S54 (2026-10-17)
- `surrender_world.py` (new parts: `make_sword`, `make_char_stake`, `make_hill_fort`; ball path `ball_pos`), `surrender_film.py`. Build: `blender -b -P surrender_film.py`
  -> `Surrender.blend`, `renders/timing_surrender.json`. Same pattern as the siege file (events by word, cameras as fractions; S49+S50 share a camera).
- Device-voice placeholders exist for S49-S58. Test stills only. Weak spots: S54 hill fort hard to see in the haze; S53 stockade out of frame.

## Udayagiri beats S55-S58 (helper agent, 2026-10-17)
- `udayagiri_world.py`, `udayagiri_film.py` (-> `Udayagiri.blend`, `renders/timing_udayagiri.json`), `compare_uday.py`. Parts defined there (to merge into the kit later):
  make_stone_wall, make_stairs, make_flagstones, make_canopy_open, make_pavilion, make_gate_doors, make_ball_pile, make_furnace, make_shed, make_scaffold,
  make_block_stack, make_gravel, make_banner, make_musketeer, make_delannoy_hatless, make_tricorn, make_sash.
- To do in the kit: a king figure in the red-gold robe (K68/K70) and a Nair with a red coat for drilled troops (K69).
