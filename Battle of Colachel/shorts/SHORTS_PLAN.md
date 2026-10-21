# Shorts for "The Battle of Colachel" (made 2026-10-21)

Why: the long video got 23 views and about 15 s average watch time in 2 days (weak opening). Shorts are a separate discovery path.
Rules used (from `_channel-context/Growth_and_Scripting_Insights.md`): motion in the first frame, an open-loop question or bold claim as the hook,
no outcome spoiled before the payoff, captions, 30-45 s, link to the full video. Each Short is a hook-rise-payoff arc.
Upload one at a time, 48 hours apart, and check analytics before the next (the file's cadence rule). Descriptions must link the full video.

Build: `python shorts/make_short.py 1_barrel|2_captain|3_twice|all` (needs the rendered clips in `shorts/render/renders/`; see below).
Layout: 1080x1920, square crop of the 1080p clip in the middle, blurred fill, hook line on top, burned-in captions, end card.
All facts and lines come from the published script (`audio/lines.txt`); narration is the real Algieba voice.

## Short 1: the barrel (about 37 s)
- **Hook (on screen, 0-3.4 s):** WHAT IF ONE CANNONBALL / HIT THE WRONG BARREL?  Teaser: the explosion, silent, then rewind.
- **Arc:** S48 (5 August 1741: a gun fires like every other day) > S49 (this ball lands on a barrel of gunpowder) > S50 (the barrel explodes; two days of fire).
- **YouTube title:** `One cannonball. One barrel. The Dutch surrendered. #shorts`
- **Description:** `August 1741, Colachel, southern India. One accidental shot into a gunpowder barrel, and a Dutch army inside a wooden wall ran out of options. Full story: [LINK TO THE FULL VIDEO] #shorts #history #battleofcolachel`

## Short 2: the captain (about 38 s)
- **Hook:** HE LOST THE BATTLE. / THE KING HIRED HIM.
- **Arc:** S55 (the king offers De Lannoy a job) > S56 (train my army; he says yes) > S58 (title: Valiya Kappithan, the Great Captain) > S60 (37 years of service, buried inside Udayagiri fort; the tomb is still there).
- **YouTube title:** `The Dutch captain who was captured, then hired by the king #shorts`
- **Description:** `Eustachius De Lannoy surrendered at Colachel in 1741. The king of Travancore gave him a job, and he stayed for about 37 years. Full story: [LINK TO THE FULL VIDEO] #shorts #history #dutch #kerala`

## Short 3: lucky shot, twice (about 30 s)
- **Hook:** A LUCKY SHOT. / THE SAME TARGET. TWICE.
- **Arc:** S26 (1740, near Kollam: a shell lands on the Travancore gunpowder store; "Remember that gunpowder store") > S51 (1741: now a lucky shot breaks the Dutch).
- **YouTube title:** `One lucky shot hit gunpowder twice (1740 and 1741) #shorts`
- **Description:** `Near Kollam in 1740 a shell blew up the Travancore gunpowder store. A year later, at Colachel, the same thing happened to the Dutch. Full story: [LINK TO THE FULL VIDEO] #shorts #history #battleofcolachel`

## Notes
- Heavy files were removed after publishing, so the 9 beat clips (S26, S48, S49, S50, S51, S55, S56, S58, S60) were re-rendered from the scenes and wavs recovered from git
  (`git show 5a82959^:<path>`); the work folder `shorts/render/` is git-ignored.
- Replace `[LINK TO THE FULL VIDEO]` with the real URL; add it as the pinned comment too.
- Add "Altered or synthetic content" disclosure as for the long video (AI narration).
