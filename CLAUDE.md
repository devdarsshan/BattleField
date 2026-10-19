# BattleField: instructions for Claude

This folder holds Dev's YouTube channel on battle history. Each video is a historical battle, told in a fixed narration style and animated in low-poly 3D with Google Flow (through the Flow MCP tool). The audience is in the US and India.

## Read these first
| File | What it is |
|---|---|
| `_channel-context/Style_Guide.md` | How the scripts are written (voice, structure, rules) |
| `_channel-context/Anti_Slop.md` | Writing patterns to avoid. Run both passes before handing over a script |
| `_channel-context/Visual_Style.md` | The low-poly 3D diorama look, and how text is handled |
| `_channel-context/Blender_Build_Rules.md` | How every Blender clip is built and checked (look, density, camera, timing) |
| `_channel-context/Production_Playbook.md` | Pipeline order, Blender/voice/render/edit/upload rules and mistakes learned from the first video. Read before starting any battle |
| `_channel-context/Flow_Workflow.md` | Step by step: characters, stills, clips, narration, cut, and the no-cut rule |
| `style-refs/` | Example images of the look |

## Folder layout
```
BattleField/
  CLAUDE.md                  this file
  _channel-context/          style, visuals, Flow workflow
  style-refs/                look reference images
  <Battle name>/             one folder per video
    <Battle>_Script.md       narration with [Sxx] beat markers
    <Battle>_Shot_List.md    characters, keyframes, and a clip-by-clip table
    Sources.md               sources, plus a table of disputed points
    frames/  clips/  audio/  final/   (Flow outputs, created as you go)
```

## Rules
1. **Continuous camera by default, cuts allowed for drastic changes.** Within a location, each clip continues the camera from the one before. A clean cut is fine (and preferred) for a big change of scale or world, such as beach diorama to parchment map (decided by the user, 2026-10-15).
1a. **Flow images first, then Blender.** For each clip, generate reference stills in Flow (free), get the user's approval, then build the clip in Blender to match them. Work one clip at a time and get sign-off before the next, to avoid rework.
2. **Free work first.** Characters and keyframe stills cost nothing. Get the user's approval on them before spending any credits on video.
3. **Ask before spending.** State the credit cost before each batch of clips. The default is 3 clips a day.
4. **Facts must be true.** Every claim needs a source in `Sources.md`. Hedge anything disputed in the narration itself ("Legend says", "Historians still argue"). Never invent numbers.
5. **Scripts run at least 10 minutes** (about 1,500+ words at 150 words a minute) unless the user asks otherwise.
6. **No text in generated images or clips.** Titles and labels are added in the edit.
7. Keep the Flow Studio key (Google AI Studio) out of chats. It lives in `~/.flow-mcp/gemini-key`.

## Starting a new battle
1. Research it and write `Sources.md`, including the disputed-points table.
2. Write `<Battle>_Script.md` following the Style Guide, then do the anti-slop passes.
3. Write `<Battle>_Shot_List.md`: characters, keyframes, and clip rows timed at about 25 words per 10-second clip.
4. Follow `_channel-context/Flow_Workflow.md`.

## Blender pipeline (trial, replaces Flow if approved)
Blender 5.2 is connected through its MCP. Project files live in `<Battle>/blender/`:
- `colachel_kit.py`: reusable low-poly assets (huts, palms, trees, boats, jetty, props, stockade, tents, royal canopy, East Indiaman ships, and figures: villagers, Dutch soldiers, Nair soldiers, commanders, the king; static crowds or walkers)
- `colachel_world.py`: the Colachel diorama (coastline terrain, faceted sea, sky, sun, haze box, village, Dutch stockade, Travancore camp, fleet)
- `film.py`: the whole film as one timeline. `CLIPS` holds each clip's frame range and narration file; `CAM_KEYS` holds the camera path (Z is metres above the ground). Run it in Blender over MCP with `exec(open(path).read())`; it rebuilds the scene and saves `Colachel.blend`
- `render_cli.py`: renders in a separate background Blender so the MCP session stays free (stills or mp4; pass absolute output paths)
- `kerala_geo.py` + `make_map_texture.py`: real Kerala coast, Ghats, rivers and lakes; the painter writes `textures/kerala_map.jpg` (the parchment map, no text). The diorama is a tile (`TILE`) standing on that map sheet at `MAP_Z`, so the camera can rise from the beach to the map without a cut
- Weather (`WEATHER` in `film.py`): storm build/hold/clear points drive the sun, sky, sea colour, haze, swells, clouds, rain and ship rocking. `shot` is the frame the Travancore gun fires
- Beats without a recording get an estimated length (`CHARS_PER_SEC`) and a Windows-voice placeholder (`make_placeholders.py`); recording the real take later re-times everything automatically
- `make_video.py`: lays the narration (`<Battle>/audio/Sxx.wav`) over the rendered picture using the `CLIPS` timings
- `renders/`: preview stills and videos
- Match the look against the Flow clips in `<Battle>/clips/`. Compare key frames side by side before rendering video.
- 24 fps, no cuts. Each clip lasts as long as its narration plus about 1 s (minimum 10 s); narration starts 0.8 s into its clip.
- Narration voice: **Algieba** (chosen by the user). Use `flow_narrate`; if it fails with "fetch failed", use `python _tools/tts.py OUT.wav "text" --voice Algieba`: the same call, and the key stays in its file.
- The Gemini free tier allows only **10 voice requests a day** (the Pro voice model allows 0). Don't spend them on tests. Beat texts live in `<Battle>/audio/lines.txt` as `Sxx|text`.
- `make_film.sh [VOICE] [NAME]` runs the whole job: record missing narration (waiting out the quota), rebuild `film.py` headless, render 1080p PNG frames (resumable), then encode with narration. Clip lengths come from the narration, so delete `renders/frames_1080p` whenever the narration changes.
- Render samples: 32 for finals (set in `film.py`), 16 is fine for previews. The PC has only Intel Arc integrated graphics: about 2.5–3.5 s per 1080p frame.
- Preview at 1280x720; re-render approved clips at 1920x1080 (re-render, never upscale).
- Never use a world volume for haze in EEVEE: it turns the render black. Use the bounded haze box.

## Current video
Live status and next steps: `Battle of Colachel/PROGRESS.md`. Keep it updated after every beat (other agents, e.g. Gemini in Antigravity, continue from it).

**Battle of Colachel (1741).** The script and shot list are done. Next step: create the characters and the 15 keyframe stills, then get the user's approval.
