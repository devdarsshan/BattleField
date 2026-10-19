# Battle of Colachel: from the last render to a published YouTube video

Your first video, so every step is here in order. Tick the boxes as you go. Copy-paste texts live in `Upload_Package.md`
(title options, description, tags, pinned comment); this guide says what to do, when, and in which order.

Current state (2026-10-19): all 69 beats have the final voice and built scenes. Rendered in 1080p: S29-S60. Rendering now:
S01-S07 and S19-S28. Still to render: S08-S18 and S61-S69.

---

## PART A: Finish the picture (on your PC and the 4050 laptop)

- [ ] **A1. Render the remaining batches** (1080p, 24 samples, `render_local.py` in each package folder):
  `rtx4050_s01_s07`, `rtx4050_s19_s28` (running), `rtx4050_s08_s18`, `rtx4050_s61_s69`.
- [ ] **A2. Collect every clip MP4 in one folder.** Names look like `clip53_S44_1080p.mp4`. There must be 69 beats, S01 to S69, one clip each
  (some beats share a clip number, for example clip 09-10 is S08). Delete any `*_bench.mp4` test files.
- [ ] **A3. Check the count and the order.** Run `python colab/merge_clips.py FOLDER final_raw.mp4`. It prints "69 clips ... beats 1..69".
  If it prints a lower number, a clip is missing: render that batch again (it resumes where it stopped).
- [ ] **A4. Watch the whole film once**, full screen, with headphones. Write down the time of anything wrong (a flicker, a floating object,
  a wrong colour, an awkward cut). Fix by rebuilding that beat's scene and re-rendering only that batch with `--only Sxx`.
  Known soft spots to look at: the S59 troop blocks (small on the map), the S61/S63 map ships, the S65-S67 sea colour, S68 sunset colours
  against the day clips.
- [ ] **A5. Check the sound.** Every clip has its own narration, so volume should match. Listen for: a clip where the voice is much louder or
  quieter, a gap or overlap at a join (each clip starts the voice 0.8 s in), a click at a cut. Fix in the editor (A7), not by re-rendering.

## PART B: Edit (add the text and polish). AUTOMATED: see `edit/README.md`

Run `edit/make_overlays.py`, `edit/make_srt.py` and `edit/edit_final.py` (3 commands) instead of doing B1-B3 and B6-B8 by hand in an editor; you still do B4, B5 and the watch-through.


The 3D clips contain **no text on purpose**. Titles, names and dates are added in an editor (DaVinci Resolve is free; CapCut and Premiere also work).
Import `final_raw.mp4` and do the following. Styles are in `_channel-context/Visual_Style.md`.

- [ ] **B1. Title card** at the very start (3 to 5 seconds, or lay it over the first seconds of S01): dark brown/charcoal map silhouette,
  "THE BATTLE OF" in small spaced capitals, a large gold serif "COLACHEL", then "Travancore vs the Dutch East India Company, 1741",
  thin gold rules, small red star. If you add it before S01, add its length to the chapter times (see C3).
- [ ] **B2. Name plates** the first time each person appears (dark plaque, thin gold border, serif capitals, italic gloss line underneath):
  Marthanda Varma (King of Travancore), Gustaaf van Imhoff (Dutch governor), Eustachius De Lannoy (Dutch captain).
  Add any other names you want (Ramayyan, the Nair soldiers, the Mukkuvar fishermen).
- [ ] **B3. Place and date labels** at the start of each segment (the script opens chapters on place-and-year fragments): for example
  "Colachel, August 1741", "Kochi, 1739", "Padmanabhapuram", "Kanyakumari, October 1741", "Mavelikkara, 1753", "Colachel today".
  Map labels (small engraved serif italics) for the map beats: Kochi, Kollam, Kayamkulam, Colachel, Ceylon, Kanyakumari, Nedumkotta.
- [ ] **B4. Check every claim on screen** against `Sources.md`. The only date to double-check is the Nedumkotta / Tipu Sultan clash
  (1789 or 1790-91); the narration says only "decades later", so leave a date off screen unless you verified it.
- [ ] **B5. Music (optional).** A quiet instrumental bed under the narration at about -25 dB makes the film feel finished. Only use music you
  have the right to: YouTube Audio Library, or a track whose licence you checked. Do not use a copyrighted song (it will be claimed or muted).
- [ ] **B6. Fades.** Fade in from black at the start, fade out to black at the end. Keep the last 20 seconds clean for the end screen (S69).
- [ ] **B7. Loudness.** Aim for about -14 LUFS integrated (the YouTube reference level), true peak under -1 dB. DaVinci: Fairlight loudness meter;
  or run `ffmpeg -i in.mp4 -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:v copy out.mp4`.
- [ ] **B8. Export.** MP4, H.264, 1920x1080, 24 fps, high bitrate (about 16 Mbps), AAC audio 192 kbps or more, stereo. Name it
  `Battle_of_Colachel_FINAL_1080p.mp4`. Watch the export once from start to end before uploading.

## PART C: Prepare the YouTube text

- [ ] **C1. Pick the title** from `Upload_Package.md` section 1 (recommended: the first one, under 100 characters).
- [ ] **C2. Description:** copy the block from `Upload_Package.md` section 2.
- [ ] **C3. Replace the chapter times with the real ones.** Run `python colab/chapter_times.py` (add the title-card length in seconds as an
  argument if you added one before S01, for example `python colab/chapter_times.py 5`). It prints the 12 chapters computed from the
  real clip lengths. With the current clips the total is about 18 minutes (the older estimate of 13.5 minutes in the upload package is out of date).
  Re-check two or three chapters against the exported video, because edits change the timing. Rules: the first chapter must be `0:00`,
  at least 3 chapters, each at least 10 seconds.
- [ ] **C4. Tags and pinned comment:** from `Upload_Package.md` sections 3 and 6.
- [ ] **C5. Thumbnail:** `thumbnail/thumbnail_1280x720.jpg` (about 245 KB, 1280x720, under YouTube's 2 MB limit) is the one with text. Text-free
  versions are in the same folder if you want to change the wording. Look at it at phone size: the text must still be readable.

## PART D: Channel and account (one time, because this is your first video)

- [ ] **D1. Verify your account with a phone number** (YouTube Studio > Settings > Channel > Feature eligibility > "Intermediate features").
  Without it you **cannot upload videos longer than 15 minutes** and cannot add a custom thumbnail. The film is about 18 minutes, so do this first.
  It takes a few minutes; the features switch on within about a day, so do it **before the upload day**.
- [ ] **D2. Channel basics:** channel name "The BattleField", profile picture, banner, a short About text (the "About the channel" paragraph in
  `Upload_Package.md` is ready), country, and contact email if you want one.
- [ ] **D3. Default upload settings** (Studio > Settings > Upload defaults): Category Education, language English, comments On,
  visibility Private (you change it to Public at the end).
- [ ] **D4. Playlist:** create "Battles of India" (Content > Playlists > New playlist).

## PART E: Upload (YouTube Studio, studio.youtube.com)

1. [ ] Click **Create > Upload videos** and choose the exported MP4. Leave the page open until the upload and the HD processing finish
   (an 18-minute 1080p file takes a while; processing "HD" completes after the upload bar finishes).
2. [ ] **Details:** paste the title and description, add the thumbnail (Upload file), pick the playlist.
3. [ ] **Audience:** "No, it's not made for kids".
4. [ ] **Altered or synthetic content:** answer honestly. The narration is an AI voice (Gemini text-to-speech) and the images are 3D animation.
   Read the question on screen and disclose the synthetic voice if it asks about realistic synthetic audio or people.
5. [ ] **Show more:** paste the tags, set language English, category Education. Leave comments On. License: Standard YouTube License.
6. [ ] **Subtitles:** open Subtitles > English > let YouTube auto-generate, then **fix the names** (Marthanda Varma, Travancore, Padmanabhapuram,
   Udayagiri, De Lannoy, Van Imhoff, Kollam, Kayamkulam, Nedumkotta, Kanyakumari, Mavelikkara, Koshy, Tipu Sultan).
7. [ ] **Video elements:** add an **end screen** over the last 18 seconds (the silent S69 sunset clip is made for it): a Subscribe element and,
   once you have another video, a video card. The Plassey call-to-action line was **cut from the narration on 2026-10-19** (the Plassey video
   does not exist yet); S69 is now a silent fade. When the Plassey video exists, put the line back in the script and re-record S69.
   Cards are optional. Add no more than a couple.
8. [ ] **Checks:** YouTube runs copyright and ad-suitability checks. Wait for "Checks complete". If it flags music, replace or remove that track.
9. [ ] **Visibility:** first keep it **Private** and watch it once from the Studio preview on your phone (audio, subtitles, thumbnail, chapters
   showing in the timeline). Then choose Public, or **Schedule** (Saturday or Sunday evening in India time gives both India and US viewers a chance).
10. [ ] **Pinned comment:** after it goes public, post the comment from `Upload_Package.md` section 6 and pin it (three dots > Pin).

## PART F: After publishing

- [ ] Share the link with a few people in the first hour (the first hours of views matter most).
- [ ] Reply to every comment in the first two days, especially corrections. Add a pinned correction if someone finds a real mistake.
- [ ] Look at Studio Analytics after 48 hours: click-through rate on the thumbnail, and where viewers stop watching. If the click-through rate is
  low (under 3 to 4%), try title 2 or 3 from the upload package, or a different thumbnail (you can swap them any time).
- [ ] Keep every file: `final_raw.mp4`, the export, the project file of the editor, and `Battle of Colachel/` in git, so you can fix and re-upload.
- [ ] Start the next video from `CLAUDE.md` ("Starting a new battle"). Plassey is the one S69 points to.

---

## Quick reference: files and commands

| What | Where |
|---|---|
| Title options, description, tags, pinned comment, Studio settings | `Upload_Package.md` |
| Real chapter times | `python colab/chapter_times.py` |
| Join all clips in order | `python colab/merge_clips.py CLIP_FOLDER final_raw.mp4` |
| Thumbnail | `thumbnail/thumbnail_1280x720.jpg` |
| Facts and disputed points | `Sources.md` |
| Style of title card, plates and labels | `../_channel-context/Visual_Style.md` |
| Render status of every beat | `PROGRESS.md` |
