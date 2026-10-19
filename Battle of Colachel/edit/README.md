# Final edit (step B of POSTING_GUIDE.md), automated

Run from this folder after all 69 clips are rendered and joined with `colab/merge_clips.py CLIPS final_raw.mp4`:

1. `python make_overlays.py`: title card, name plates and place/date labels (PNG) and `overlays.json` with their times.
   Edit the PLATES / LABELS lists at the top of the file to change text or timing. Times follow the real clip lengths.
2. `python make_srt.py`: `Battle_of_Colachel.srt`, English subtitles with the correct names, timed from the narration.
   Upload it in YouTube Studio > Subtitles > Upload file > With timing.
3. `python edit_final.py final_raw.mp4 Battle_of_Colachel_FINAL_1080p.mp4`: 5 s title card + film + overlays + fade in/out +
   loudness -14 LUFS, H.264 1080p 24 fps 16 Mbps. Add `--preview 120` to export only the first 120 s as a check.

Chapter times for the description: `python ../colab/chapter_times.py 5` (the 5 is the title-card length).
Not done here (needs your eyes): map labels over the map clips (positions depend on the camera), music, a final watch-through.
