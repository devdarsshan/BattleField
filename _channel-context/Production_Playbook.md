# Production playbook (all videos)

What the first video (Battle of Colachel: 69 beats, 18 minutes, published October 2026) taught us. Follow this for every new battle.
Style rules stay in `Style_Guide.md`, `Visual_Style.md` and `Blender_Build_Rules.md`; this file adds the pipeline, the numbers and the mistakes
that cost time. If the user says something different, the user wins; write the decision into the battle's `PROGRESS.md`.

## 1. The order of work (and who approves what)
1. Research, `Sources.md`, then the script (anti-slop passes), then the shot list. Script is 10+ minutes; scripts are cut into beats `S01..Snn`.
2. **Plan the whole batch before building** (sets reused vs new, new kit parts, camera idea per beat). Build shared kit parts first, once.
3. Flow reference stills per clip (free) -> **user approves** -> Blender build against the approved still, side by side.
4. Voice: record in beat order, in batches (section 3). The real narration length drives every clip length.
5. Rebuild scenes with the final voice, render per batch (section 4), review, merge, edit (section 6), upload (section 7).
6. Update the battle's `PROGRESS.md` after every beat (other agents continue from it).

**Quality bar (the user flagged this repeatedly):** "no weak stops." Do not hand over a set until the weak spots are fixed: empty ground,
flat colours, frozen figures, tile or horizon edges, a camera that shows unbuilt ground. Check each beat on real frames before saying done.

## 2. Blender: rules learned on top of `Blender_Build_Rules.md`
- **One world.** Reuse the kit (`colachel_kit.py` equivalent), the shared lighting (`scene_base`), the sea, the palette and the figures. Add new parts to the kit; never copy into a scene file.
- **The camera may only look at built ground.** Before animating, probe-render a few stills (960x540, 12 samples) from the keyframe positions and from the
  END of every move. S67's rise out over the sea showed a hard sea-tile edge, a flat green plane and bare pyramids because the camera turned toward
  unbuilt land; the fix was to turn it inland over the monument where the village was built. Rule: end moves over built areas, never along an unbuilt coast.
- **Surroundings are mandatory.** Every set needs its horizon: far sea plane below the tile, far land strips and hills, a sky gradient. No visible tile edges,
  no flat "slab" ground. Interiors and dioramas still need things outside the window or at the table's edge (`surround.py`, `scene_envs.py`).
- **Light:** emissive objects (sun discs, glowing sky parts) must have `visible_shadow = False`, or they cast dark maroon shadows. Use the bounded haze box,
  never a world volume (EEVEE turns black). Keep sunset colours consistent with the neighbouring day clips (check S68 vs S67 style).
- **Clear trees and props along the camera path**, and check that nothing fills the lens.
- **Resolution matters:** judge detail at 1080p, not 720p. Small crowds (troop blocks on maps) and distant ships look weak at 1080p; make them bigger or closer.
- **Maps:** top-down, north up; labels are added in the edit, not in 3D (needs the final frames to place them).
- **Endings:** a closing scene should reuse an existing built area, not a new one-off set (the sunset-stumps ending was rejected).
- **Render each beat as its own job** (own frames folder, own mp4) so a rework redoes only that beat. Keep the old take until the new one is approved.
- Scenes are rebuilt headless with `blender -b -P <scene>_film.py`; clip frame ranges follow the narration, so rebuild after any re-record.

## 3. Voice (Gemini TTS, voice Algieba)
- Free tier: **10 requests per day per Google project** (HTTP 429 `GenerateRequestsPerDay...`). The quota is a rolling window, not a midnight reset.
- `_tools/tts.py` reads several keys (`~/.flow-mcp/`); each extra key from a *different project* adds 10 a day. Never paste keys into chat.
- `python _tools/record_batch.py S08 S09 ...` records lines from `audio/lines.txt` (`Sxx|text`). Do not spend requests on tests.
- A 69-beat film needs about 7 days on one key, 4 with two. Start recording early, in story order, and rebuild scenes only after the take exists.
- Keep old takes in `audio/<voice>/`; a removed line goes to `audio/archive_removed/` (we cut the Plassey call-to-action and kept S69 silent).

## 4. Rendering (numbers from this film)
- Finals: **1080p, 24 samples, 24 fps**. Colab 720p / 16 samples is for previews only.
- RTX 4050 laptop: about 1-2 s/frame at 1080p (benchmark first with `render_local.py --bench 48`; Windows must be set to use the NVIDIA GPU for `blender.exe`).
  Intel iGPU PC: about 1.6-2.7 s/frame on simple scenes, much slower on dense ones. One render at a time per GPU.
- Per-batch package: `colab/build_rtx_package.py LO HI` -> folder + zip (blends, wavs, `manifest.json`, `render_cli.py`, `render_local.py`). Do not commit zips (GitHub 100 MB limit).
  Resumable: frames over 2 KB are skipped on restart. **Never rebuild a package folder that already holds finished renders** (the builder deletes the folder).
- **Video format: H.264 (libx264), CRF 18, yuv420p, AAC, 1080p 24 fps. Never `mpeg4`.** The Colab engine once fell back to `mpeg4` (S08-S18 came out soft) and no longer may.
  After any batch run `ffprobe` on the clips: it must say `h264,1920,1080,24/1`.
- Colab: use `colab/colab_render_final.ipynb`; check the log shows `codec: libx264`; copy results to Drive as they finish.
- Delete frame folders once the mp4 is encoded and approved; they are gigabytes. Keep timing JSONs.

## 5. Merging and checking
- `colab/merge_nested.py FOLDER OUT.mp4 [--max-beat N]` joins clips found in sub-folders in beat order and converts any non-H.264 clip first.
- It needs all beats; it ignores `*_bench.mp4`. Probe durations against `renders/timing_*.json` (they must agree within 0.1 s).
- Watch the joined film once: picture, voice level, joins, labels. Known soft spots go on a list and are fixed per beat.

## 6. Edit (automated, `edit/` of the battle)
- 3D clips contain **no text**. `make_overlays.py` makes the title card (5 s), name plates (first time a person is named) and place/date labels (one list at the top;
  times follow the real clip lengths); `make_srt.py` makes subtitles from the narration; `edit_final.py` assembles with fades and **-14 LUFS** loudness (16 Mbps H.264).
- Check plates on real frames: not over faces. Map labels need the final map frames to place them.
- Chapters: `chapter_times.py <title-card seconds>`; **the first chapter must be 0:00**, at least 3 chapters, each at least 10 s.
- No music unless licensed (YouTube Audio Library). The Plassey (next battle) call-to-action stays out until that video exists.

## 7. Upload (first-video lessons)
- Phone-verify the channel first (needed for videos over 15 minutes and custom thumbnails; can take a day).
- Order: upload file -> title/description (paste file `YOUTUBE_PASTE.md`) -> thumbnail -> playlist -> not made for kids -> altered/synthetic content (AI voice: disclose)
  -> tags -> subtitles **Upload file > With timing** (`.srt`) -> end screen over the last 18 s -> Private check on phone -> Public or Schedule -> pinned comment (after public).
- Make 3 thumbnail text variations from text-free stills (`edit/make_thumbnails.py`); YouTube "Test & compare" can A/B them.
- Title: search words + hook, under 100 characters. Never claim "first Asian victory over a European power" style overclaims; say disputed points in the narration.

## 8. Files and housekeeping
- Git keeps scripts, docs, small reference images and timing JSONs. Videos, frames, zips and big renders are ignored. Do not leave Blender `.blend1` backups or test renders.
- After publishing, archive heavy files into one folder outside the repo and copy it to Drive: final clips (not intermediates), narration wavs, `.blend` files.
  Delete: joined intermediates, package folders and zips, preview renders, `.blend1`, frame folders, old voice samples.
- Size budget per video after cleanup: about 1 GB (clips 0.8 GB + wavs 0.2 GB + blends 0.2 GB).
- Keep `PROGRESS.md` current; write decisions (cuts, replaced beats) into it with the date.

## 9. Starting the next battle
1. Copy the pipeline scripts, do not edit them in place: `colab/render_local.py`, `colab/build_rtx_package.py`, `colab/merge_nested.py`, `colab/chapter_times.py`,
   `edit/` (overlays, srt, final), `edit/make_thumbnails.py`, `_tools/tts.py`, `_tools/record_batch.py`. Replace "Colachel" names and the beat/TIMING maps.
2. Start the shared kit from the Colachel kit (figures, palms, boats, ships, tents, stockade, canopy, sea, sun) so the new video looks like the same channel.
3. Reuse this playbook's order: research -> script -> shot list -> Flow refs -> Blender -> voice -> render -> edit -> upload.
