# Shorts for "The Battle of Colachel" (made 2026-10-21, all three approved by the user)

Why: the long video got 23 views and about 15 s average watch time in 2 days (weak opening). Shorts are a separate discovery path.
Rules used (from `_channel-context/Growth_and_Scripting_Insights.md`): motion in the first frame, an open-loop question or bold claim as the hook,
no outcome spoiled before the payoff, captions, 30-45 s, link to the full video. Each Short is a hook-rise-payoff arc.

## Where the files are
| What | Path (inside `Battle of Colachel/shorts/`) |
|---|---|
| Finished Shorts (1080x1920, MP4) | `out/short_1_barrel.mp4`, `out/short_2_captain.mp4`, `out/short_3_twice.mp4` |
| Preview frames | `out/prev_*.png`, `out/preview_*.png` |
| Re-rendered 1080p beat clips (S26, S48-S51, S55, S56, S58, S60) | `render/renders/clip*_S*_1080p.mp4` |
| Recovered scenes and narration used for the re-render | `render/*.blend`, `render/S*.wav` |
| Builder script | `make_short.py` (`python make_short.py 1_barrel`, `2_captain`, `3_twice` or `all`) |
`out/` and `render/` are git-ignored (large). Copy `out/` to Drive to keep the Shorts.

## Upload order (one at a time, 48 hours apart; check Studio before the next)
Check "viewed vs swiped away" and average view duration first. If a Short is clearly working, wait longer before the next.
1. Short 1, the barrel: the strongest hook, needs no context.
2. Short 3, lucky shot twice (48 h later): a callback to the Kollam shot.
3. Short 2, the captain (48 h after that).

## Studio settings for each Short
- Upload on desktop (Create > Upload videos); vertical and under 3 minutes makes it a Short automatically.
- Show more > Related video: link the full video.
- Audience: not made for kids. Altered or synthetic content: yes (AI narration).
- Check once as Private on a phone, then Public. After it is public, post the pinned comment and pin it.

Replace `[YOUR VIDEO LINK]` below with the full video's URL.

## Short 1: the barrel (35.5 s) `out/short_1_barrel.mp4`
- Hook on screen: WHAT IF ONE CANNONBALL / HIT THE WRONG BARREL? (silent explosion teaser, then rewind)
- Arc: S48 (5 August 1741, a gun fires like every other day) > S49 (this ball lands on a barrel of gunpowder) > S50 (the barrel explodes; two days of fire).
- **Title:** `One cannonball. One barrel. The Dutch surrendered. #shorts`
- **Description:**
```
August 1741, Colachel, southern India. One accidental shot into a gunpowder barrel, and a Dutch army inside a wooden wall ran out of options.

Full story (18 min): [YOUR VIDEO LINK]

#shorts #history #battleofcolachel
```
- **Pinned comment:** `The full story, with the monsoon, the fishermen and the Dutch captain who stayed for 37 years: [YOUR VIDEO LINK]`

## Short 3: lucky shot, twice (27.1 s) `out/short_3_twice.mp4`
- Hook on screen: A LUCKY SHOT. / THE SAME TARGET. TWICE.
- Arc: S26 (1740, near Kollam: a shell lands on the Travancore gunpowder store; "Remember that gunpowder store") > S51 (1741: now a lucky shot breaks the Dutch).
- **Title:** `One lucky shot hit gunpowder twice (1740 and 1741) #shorts`
- **Description:**
```
Near Kollam in 1740 a shell blew up the Travancore gunpowder store. A year later, at Colachel, the same thing happened to the Dutch.

Full story (18 min): [YOUR VIDEO LINK]

#shorts #history #battleofcolachel
```
- **Pinned comment:** same as Short 1.

## Short 2: the captain (37.0 s) `out/short_2_captain.mp4`
- Hook on screen: HE LOST THE BATTLE. / THE KING HIRED HIM.
- Arc: S55 (the king offers De Lannoy a job) > S56 (train my army; he says yes) > S58 (title: Valiya Kappithan, the Great Captain) > S60 (about 37 years of service, buried inside Udayagiri fort; the tomb is still there).
- **Title:** `The Dutch captain who was captured, then hired by the king #shorts`
- **Description:**
```
Eustachius De Lannoy surrendered at Colachel in 1741. The king of Travancore gave him a job, and he stayed for about 37 years.

Full story (18 min): [YOUR VIDEO LINK]

#shorts #history #dutch #kerala
```
- **Pinned comment:** same as Short 1.

## Notes
- Facts and lines come from the published script (`audio/lines.txt`); narration is the real Algieba voice (recovered wavs).
- Heavy files were removed after publishing, so the 9 beat clips were re-rendered from scenes and wavs recovered from git (`git show 5a82959^:<path>`).
- Log the Shorts' results (views, swipe-through, average view duration) in `PROGRESS.md` after 48 hours.
