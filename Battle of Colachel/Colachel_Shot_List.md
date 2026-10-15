# Battle of Colachel: Continuous Shot List

One unbroken camera move for the whole film, with no cuts. The whole story takes place in a single low-poly 3D diorama of the Kerala coast that sits on an old parchment map. To change location, the camera rises up to map height, glides across the map, and comes back down. It never cuts.

- **Clips:** 82 clips, each 10 seconds long, about 13.7 minutes in total, timed to the script at about 150 words a minute.
- **Cost:** about 15 credits per clip, so about 1,230 credits. On the free 50 credits a day, that is about 25 days of generating. A paid Google AI plan makes it much faster.
- **Look:** follow `../_channel-context/Visual_Style.md`. Generate no text inside any image or clip.

## Continuity rules (follow every time)

1. **Exact join on every clip.** Clip N+1 uses the **real last frame of clip N** as its first frame (`chain_previous`). Never start a clip from a fresh image.
2. **Check before the next clip.** Before generating clip N+1, look at the last frame of clip N. If a main character's face is turned away or too small, regenerate clip N so it ends with the face clear. The next clip only knows what a character looks like from that frame.
3. **Keyframes as targets.** At each keyframe listed below, set that keyframe as the clip's `last_frame` so the chain lands exactly on the approved image. This stops the look drifting over 82 clips.
4. **New characters.** When a character appears for the first time (Marthanda Varma in clip 03, van Imhoff in clip 26, De Lannoy in clip 39), use `flow_continue`. It keeps the start frame and adds the saved character, so the join stays exact.
5. **Leave text out.** Name plates, the title card, dates and map labels are added in the edit, using the styles in the style refs.
6. **Ask before spending.** Get the user's approval of all keyframe stills (free) before generating any clip. Generate clips in batches of 3 a day, about 45 credits, unless the user says otherwise.

## Characters to create first (free)

| Name | Look |
|---|---|
| Marthanda Varma | King of Travancore, mid-30s, dark brown skin, moustache, bare chest with gold necklaces and armlets, white mundu (wrapped cloth), red-and-gold sash, curved sword |
| Eustachius De Lannoy | Dutch officer, about 25, pale skin, dark blue VOC coat with brass buttons, white cross-belts, black tricorn hat, sword |
| Gustaaf van Imhoff | Dutch governor, about 35, pale skin, powdered white wig, long dark coat, lace cuffs |
| Nair soldier (generic) | Bare chest, white-and-red cloth, round shield, short sword or spear |
| Dutch soldier (generic) | Blue coat, tricorn hat, musket |
| Mukkuvar fisherman (generic) | Dark skin, simple white cloth around the waist, rope net |

## Keyframe stills to approve first (free)

| Key | Lands at end of clip | Image |
|---|---|---|
| K01 | start of clip 01 | Calm dawn sea, Colachel's palm-lined beach and fishing village ahead |
| K02 | 03 | Travancore camp in the palms, Marthanda Varma under his canopy |
| K03 | 08 | Very high view: the beach becoming the parchment map |
| K04 | 15 | Top-down parchment map of the Kerala coast, Kochi fort in orange |
| K05 | 19 | Padmanabhapuram wooden palace town from above |
| K06 | 29 | Van Imhoff and Marthanda Varma meeting under a canopy |
| K07 | 33 | Powder-store explosion near Kollam |
| K08 | 38 | Dutch boats landing on Colachel beach, ships behind |
| K09 | 46 | Temple at Thiruvattar, the king with his sword |
| K10 | 47 | Monsoon: rough grey sea, rain on the beach |
| K11 | 53 | Fishermen with palm-trunk "cannons" on the dunes |
| K12 | 61 | Explosion and fire inside the stockade |
| K13 | 66 | Udayagiri hill fort with the prisoner column |
| K14 | 69 | European-style musket drill on the parade ground |
| K15 | 82 | Sunset over the empty beach where the stockade stood |


## Clip table

Every clip **starts on the last frame of the clip before it**. The visual column describes what the clip moves toward.

| Clip | Beat | Place | Visual (moves toward) | Camera |
|---|---|---|---|---|
| 01 | S01 | Colachel beach, dawn | Black screen fades up on calm sea at dawn, low over the water -> low-poly fishing village and palm-lined beach of Colachel ahead | slow push in over waves |
| 02 | S02 | Colachel beach | Beach -> sharpened wooden-post stockade on the sand; Dutch soldiers in blue coats and tricorn hats behind it | glide along the stockade wall, slight high angle |
| 03 | S03 | Colachel beach | Over the stockade wall -> Travancore army camped in the palm groves outside; Marthanda Varma under a canopy among his commanders | rise over the wall, drift inland to the king |
| 04 | S04 | Colachel beach | Marthanda Varma -> pan out to sea: Dutch warships anchored offshore with cannons | pan from king to sea |
| 05 | S05 | Colachel beach | Grey monsoon sea, big waves, ships rocking far out -> back inside the stockade: soldiers sitting by nearly empty rice sacks | swing back from sea into the stockade |
| 06 | S06a | Colachel beach | Inside stockade, a Travancore cannon on the hillside behind palms puffs smoke -> camera rises high above the beach; dark title space in the sky (title card added in edit) (part 1 of 2) | crane up and back, very high |
| 07 | S06b | Colachel beach | Inside stockade, a Travancore cannon on the hillside behind palms puffs smoke -> camera rises high above the beach; dark title space in the sky (title card added in edit) (part 2 of 2) | crane up and back, very high |
| 08 | S07 | Map | From high above, the beach shrinks and the land becomes the parchment map of Kerala with north at top | continue rising to straight top-down |
| 09 | S08a | Map | Top-down parchment map: thin coastal strip, sea on left, green low-poly hills (Western Ghats) on right, palms and blue rivers as small 3D props (part 1 of 2) | slow glide north along the coast |
| 10 | S08b | Map | Top-down parchment map: thin coastal strip, sea on left, green low-poly hills (Western Ghats) on right, palms and blue rivers as small 3D props (part 2 of 2) | slow glide north along the coast |
| 11 | S09a | Map -> hills | Descend into the hills: low-poly pepper vines on trees, baskets of black pepper (part 1 of 2) | dip down into the hills |
| 12 | S09b | Map -> hills | Descend into the hills: low-poly pepper vines on trees, baskets of black pepper (part 2 of 2) | dip down into the hills |
| 13 | S10 | Map | Rise back up: small kingdoms appear as coloured low-poly forts dotted along the coast | rise and drift along the coast |
| 14 | S11a | Map | Kochi fort turns orange (Dutch); tiny Dutch ships moored (part 1 of 2) | push in on Kochi |
| 15 | S11b | Map | Kochi fort turns orange (Dutch); tiny Dutch ships moored (part 2 of 2) | push in on Kochi |
| 16 | S12a | Map | Dutch officials and small rajas at a table in Kochi, pepper sacks going onto Dutch ships -> pull back to the map, forts all small (part 1 of 2) | pull back to map height |
| 17 | S12b | Map | Dutch officials and small rajas at a table in Kochi, pepper sacks going onto Dutch ships -> pull back to the map, forts all small (part 2 of 2) | pull back to map height |
| 18 | S13 | Map | Glide south to the tip of the coast: Travancore | glide south |
| 19 | S14 | Padmanabhapuram | Descend to a low-poly wooden palace town; Marthanda Varma (young) on a palace veranda | descend and push in |
| 20 | S15 | Padmanabhapuram | Palace courtyard: nobles in a tense group, then guards lead them away; king stands alone | slow orbit |
| 21 | S16a | Map | Rise to the map: Travancore colour spreads north over Attingal, Nedumangad, Kottarakkara (part 1 of 2) | rise, glide north |
| 22 | S16b | Map | Rise to the map: Travancore colour spreads north over Attingal, Nedumangad, Kottarakkara (part 2 of 2) | rise, glide north |
| 23 | S17 | Map | Pepper sacks in conquered lands now go onto red-flagged English ships instead of Dutch ones | track along a coastal port |
| 24 | S18 | Map | Travancore territory grows; Kochi orange fort looks small beside it | pull back wide |
| 25 | S19 | Map | Glide out to sea to the south-east: the island of Ceylon; a Dutch ship sails from it toward Kochi | glide over sea and back |
| 26 | S20 | Kochi | Descend into the Kochi fort: van Imhoff (Dutch governor, wig, long coat) at a desk writing by candle | descend into a room through a window |
| 27 | S21 | Kochi -> meeting | Van Imhoff and Marthanda Varma face each other across a low table under a canopy; Imhoff points firmly | continuous move from desk to meeting tent |
| 28 | S22a | Meeting | Same meeting: the king calm, gestures to the forests behind; Imhoff stiff (part 1 of 2) | slow orbit around the two |
| 29 | S22b | Meeting | Same meeting: the king calm, gestures to the forests behind; Imhoff stiff (part 2 of 2) | slow orbit around the two |
| 30 | S23 | Meeting | Close on the king, calm, arms folded | slow push in |
| 31 | S24 | Map | Imhoff walks out, tent fades below as camera rises; on the map a Dutch war banner rises at Kochi, a line of soldiers marches south | rise to map |
| 32 | S25 | Near Kollam | Descend to fields near Kollam: Dutch and allied troops advance in lines toward Travancore troops | descend to battlefield |
| 33 | S26 | Near Kollam | A shell arcs into a Travancore powder store; puff of low-poly explosion; soldiers run; cannons left behind | track the shell |
| 34 | S27 | Varkala | Allies march south along cliffs; at Varkala a wall of Nair soldiers with swords and round shields stops them; allies turn back | glide south along cliffs |
| 35 | S28 | Map | Rise to map: armies shuffle back and forth around Kollam | rise to map |
| 36 | S29 | Map | A Dutch ship from Ceylon arrives at Kochi; a dotted route arrow swings south toward the tip | follow ship, then arrow |
| 37 | S30 | Off Colachel | Dutch warships off Colachel fire on the shore; smoke puffs | descend to sea level |
| 38 | S31 | Colachel beach | Seven large ships and many boats; soldiers wade ashore onto the sand | track boats to shore |
| 39 | S32 | Colachel beach | De Lannoy (young officer, blue coat, sash) on the beach giving orders, pointing at the ground | push in on De Lannoy |
| 40 | S33 | Map | Rise to map: Colachel beach, rice fields and palms behind, Padmanabhapuram palace about 13 km inland marked | rise to map, glide inland and back |
| 41 | S34 | Colachel -> Kottar | Descend to the beach: stockade being built; then glide inland as Dutch soldiers take village after village | descend then track inland |
| 42 | S35a | Kottar | Dutch column near Kottar; palace roofs visible in distance (part 1 of 2) | rise slightly, look toward the palace |
| 43 | S35b | Kottar | Dutch column near Kottar; palace roofs visible in distance (part 2 of 2) | rise slightly, look toward the palace |
| 44 | S36a | Kalkulam | Glide to Kalkulam: Marthanda Varma arrives, crowds of Nair fighters gather (part 1 of 2) | glide inland |
| 45 | S36b | Kalkulam | Glide to Kalkulam: Marthanda Varma arrives, crowds of Nair fighters gather (part 2 of 2) | glide inland |
| 46 | S37 | Thiruvattar temple | Low-poly temple; king lays his sword before the shrine at dawn | push in |
| 47 | S38 | Coast | Camera rises; dark monsoon clouds roll in, rain, sea turns rough, waves hit the beach | rise, turn to sea |
| 48 | S39 | Map | Wide over the sea: Ceylon far away, a Dutch ship turns back in the storm | glide over the sea |
| 49 | S40 | Colachel area | Back over land: Travancore army pushes Dutch out of villages back to the beach | glide back to coast |
| 50 | S41 | Colachel beach | Travancore army surrounds the stockade in a ring; camp fires | slow orbit around the ring |
| 51 | S42 | Colachel beach | Orbit continues to the fishing village beside the beach | continue orbit |
| 52 | S43 | Fishing village | Mukkuvar fishermen by their boats; a Dutch officer offers a coin bag, they turn away | push in |
| 53 | S44 | Fishing village | Fishermen push carts with palm trunks shaped like cannons onto the dunes | track the carts |
| 54 | S45 | Dunes | Fake cannons on the dunes from behind; camera holds | slow drift |
| 55 | S46a | Sea | Two small Dutch ships approach; Travancore guns fire from the shore; ships turn away (part 1 of 2) | pan from shore guns to ships |
| 56 | S46b | Sea | Two small Dutch ships approach; Travancore guns fire from the shore; ships turn away (part 2 of 2) | pan from shore guns to ships |
| 57 | S47 | Stockade | Inside the stockade in rain: soldiers count the last rice sacks | descend into the stockade |
| 58 | S48 | Hillside battery | Travancore cannon fires from the hillside | pull out over the wall to the battery |
| 59 | S49 | Stockade | Follow the glowing ball into a powder barrel inside the stockade | track the ball |
| 60 | S50a | Stockade | Explosion, fire spreads, rice stores burn (part 1 of 2) | pull back slowly |
| 61 | S50b | Stockade | Explosion, fire spreads, rice stores burn (part 2 of 2) | pull back slowly |
| 62 | S51a | Stockade | Smoke drifts over the stockade (narration callback, no new action) (part 1 of 2) | slow rise |
| 63 | S51b | Stockade | Smoke drifts over the stockade (narration callback, no new action) (part 2 of 2) | slow rise |
| 64 | S52 | Stockade | Dutch raise a white flag over the smoking stockade | push in on flag |
| 65 | S53 | Beach | Dutch officers including De Lannoy hand over swords to Travancore commanders | slow orbit |
| 66 | S54 | Udayagiri | Prisoners marched inland to a hill fort (Udayagiri) | track the column into hills |
| 67 | S55 | Udayagiri | Inside the fort: the king faces De Lannoy | push in |
| 68 | S56 | Udayagiri | De Lannoy bows | hold, slight orbit |
| 69 | S57 | Drill ground | Soldiers drilling in musket lines; cannon crews; De Lannoy directs | pull out to drill ground |
| 70 | S58 | Drill ground | King places a gold sash on De Lannoy | push in |
| 71 | S59a | Map | Rise to map: Travancore colour spreads north over Kollam and Kayamkulam; a long wall line (Nedumkotta) draws across the north (part 1 of 2) | rise to map, glide north |
| 72 | S59b | Map | Rise to map: Travancore colour spreads north over Kollam and Kayamkulam; a long wall line (Nedumkotta) draws across the north (part 2 of 2) | rise to map, glide north |
| 73 | S60 | Udayagiri chapel | Glide back south and descend to a small chapel inside Udayagiri fort; a stone tomb | descend and push in |
| 74 | S61 | Map | Rise to map: Dutch ships leave Kanyakumari at the southern tip | rise and glide to the tip |
| 75 | S62 | Mavelikkara | Treaty tent: Dutch and Travancore envoys sign a scroll | descend into tent |
| 76 | S63 | Map | Pull up: Travancore now the biggest colour on the coast; pepper ships flow to it | rise to map |
| 77 | S64 | Thiruvananthapuram | Descend to the Padmanabhaswamy temple; the king lays down his sword at the door | descend |
| 78 | S65 | Colachel beach, today | Glide back to Colachel beach in daylight: a victory pillar on the sand | glide along the coast |
| 79 | S66 | Colachel beach | Slow orbit of the pillar | slow orbit |
| 80 | S67a | Colachel beach | Camera rises from the pillar out over the sea (part 1 of 2) | slow rise |
| 81 | S67b | Colachel beach | Camera rises from the pillar out over the sea (part 2 of 2) | slow rise |
| 82 | S68 | Colachel beach | Sunset over the empty beach where the stockade stood; fade to black (end) | hold, gentle drift, fade |