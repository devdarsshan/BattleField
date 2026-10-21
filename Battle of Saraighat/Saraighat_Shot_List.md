# Battle of Saraighat (1671): Shot List

One row per script beat (42 beats). Built for the current pipeline: **Flow reference stills (free) > user approval > Blender build to match > voice > render > edit** (`../_channel-context/Production_Playbook.md`, `Blender_Build_Rules.md`).

- **Estimated length: 12:33** including the 18 s end screen (limit 10 to 13 minutes). Each beat is its narration at about 132 words a minute plus about 1.8 s, minimum 10 s. The real Algieba takes will re-time everything; the "Starts" column is for checking the hook and pacing.
- **Hook check:** S01 is on screen at 0:00 with the strongest image (the sick commander above the river, his fleet running, the Mughal fleet coming). The question lands inside the first 30 s. The **title card (under 2 s) goes between S02 and S03**, never before.
- **Cuts:** continuous camera within a set; a clean cut or cloud dissolve when the place or scale changes (marked in the Join column).
- **No text** in any still or render. Names, dates, map labels and the title card are added in the edit.
- **Facts:** every picture must match the script and `Sources.md`. Where a beat is told as tradition (the uncle, the arrow letter, the hookah), show it plainly and let the narration carry the hedge.

## Look and colours
- Same channel look as Colachel: low-poly, flat-shaded, matte, warm low sun, bounded haze box, AgX Medium Low Contrast (outdoor) / Base Contrast (map, interiors).
- **Ahom side = red and white** (white cotton with red borders and sashes, red banners; red on the map). **Mughal side = green** (green banners, green and white coats and turbans; green on the map). Rajput cavalry in saffron and white under green Mughal banners.
- Assam, not Kerala: broadleaf forest, bamboo clumps, areca palms (thin, tall), banana plants, tall grass on the sandbars, green hills that rise steeply from the water. Wet light: haze, low cloud on the hills, rain in S08, S14, S26-S29.
- The river is wide and grey-green, using the faceted water from the kit (`make_faceted_sea`) with a river colour and a gentle flow, not sea swell.

## Sensitivities (read before making any still)
- **Guru Tegh Bahadur (S15) is not shown as a figure.** Sikh tradition objects to images of the Gurus. Show only the army column and a separate, distant camp; the narration carries the mention.
- **The uncle (S18):** the sword is raised and the camera turns away to the wall. No strike, no blood.
- **Alaboi (S21), the night raid (S22), the admiral (S33):** no gore. Falling banners, dust, smoke, a slumped figure.
- **The princess (S09):** a closed palanquin only, no person shown.
- Keep the story about the river and the men. No religious buildings used as symbols for either side.

## Characters (Flow character refs first, then one kit figure each)
| Name | Look | First seen |
|---|---|---|
| Lachit Borphukan | Ahom commander, about 45-50, lean, strong jaw, thin moustache, white cotton jacket and dhoti with red borders, red sash, white turban; the gold-handled hengdang sword. Feverish and pale in S01, S27-S31 | S01 |
| Chakradhwaj Singha | Ahom king, middle-aged, richer white and gold silk, gold ornaments, tall white turban | S10 |
| Udayaditya Singha | The next king: same royal dress as Chakradhwaj, younger, slimmer (one kit figure with a variant) | S25 |
| Atan Burhagohain | Chief minister, older, grey beard, plain white robes, calm | S24 |
| Raja Ram Singh | Rajput prince of Amber, about 40, full beard, saffron and white jama (long coat), jewelled turban with a plume, sword; rides a white horse | S13 |
| Munawwar Khan | Mughal admiral, heavy-set, green and gold coat, turban; seated on a carpet on his big boat with a hookah | S33 |
| Ahom soldier / rower (generic) | White cotton, red sash, bare arms, dao (straight broad sword), bow or spear; rowers bare-chested | S01 |
| Mughal soldier (generic) | Green and white coat, turban, matchlock or spear | S04 |
| Rajput horseman (generic) | Saffron and white, turban, lance, small round shield | S13 |

## Sets (plan the batch before building; build the shared kit parts first)
| Set | What it is | Beats | New or reused |
|---|---|---|---|
| **A. The Guwahati narrows** | The main diorama: the Brahmaputra squeezed between hills; Itakhuli hill and fort on the south bank with Lachit's hill camp, Aswakranta on the north bank, earthen ramparts joining the hills, sandbars, villages, both fleets. Day, night, dawn and dusk lighting | S01-S02, S05, S12, S16-S19, S26-S35, S38-S42 | **New**. The biggest build. Reuse kit palms, huts, boats, figures, the faceted water and `scene_base` |
| **B. The valley map** | Parchment map of the Brahmaputra valley, north up: river, hills as 3D props, Guwahati, Garhgaon, Jorhat, the Manas river, Bengal to the west. Red/green colour washes and troop blocks | S03-S04, S06-S07, S09, S15, S37 | **New map texture** (new geo data like `kerala_geo.py`); reuse the map pipeline (`map_world`, `make_map_texture`) |
| **C. Garhgaon** | The Ahom capital: wooden palace on a raised plinth, gateway, town; Mughal troops at the gate, then rain | S08 | New, small |
| **D. Ahom court** | Palace hall interior: pillars, throne platform, nobles kneeling. Must have surroundings outside the doors | S10-S11, S24-S25 | New, small (reuse canopy, court robes from kit) |
| **F. Mughal camp** | Ram Singh's camp: big tents, horse lines, cannon, campfires; night version for the raid | S13-S14, S22, S36 | New; reuse kit tents and cannon |
| **G. Alaboi plain** | Open grassy plain with low hills behind, for the cavalry charge | S20-S21 | New, simple terrain, many figures |
| **H. Ahom camp at night** | Small camp under the hill: huts, fires, guards (the arrow letter) | S23 | Part of set A at night |

## New kit parts (build once, before any scene)
1. **Ahom war boat:** long, narrow, low, many rowers, a small raised deck at the stern; several sizes.
2. **Mughal war boat:** big, wide, high-sided, with rows of cannon (up to 16) and a cabin; flags plain green.
3. **Boat bridge:** Ahom boats lashed side by side with planks across (built from item 1).
4. **River water:** the faceted sea with a river colour, flow direction and gentle ripples.
5. **Earthen rampart:** long raised mound with a ditch and a bamboo palisade on top.
6. **Assam vegetation:** bamboo clumps, areca palms, banana plants, broadleaf trees, tall riverbank grass.
7. **Figures:** Ahom soldier, rower, noble, king; Mughal soldier; Rajput horseman; the named characters above. Add to the kit as new kinds, never as scene copies.
8. **Horses** for the Rajput cavalry (check what the kit has; add a low-poly horse and rider if not).

## Keyframe stills to approve first (Flow, free)
| Key | Used for | Image |
|---|---|---|
| K01 | S01, S27-S29 | Hook: a sick commander on a mat under a thatched shelter on a hilltop above a wide river; below, small boats rowing upstream and a wall of big war boats with cannon smoke coming from downstream. Late afternoon, haze |
| K02 | S02, S26, S30-S31 | Six or seven small, long Ahom boats at the foot of the hill, one commander standing in the prow, the big fleet behind |
| K03 | S03-S04, S06 | Top-down parchment map of a long river valley running east-west, green 3D hills both sides, a cluster of hills pinching the river near the west end |
| K04 | S05, S17, S40-S41 | The narrows from above: river about one kilometre wide between steep green hills on both banks, ramparts between the hills, boats on the water |
| K05 | S07, S09, S37 | The map with a long column of green troop blocks and boats moving up the river; the eastern half red |
| K06 | S08 | The Ahom capital: wooden palace on a raised plinth, green-bannered soldiers at the gate, a royal party leaving up a forest road, rain coming |
| K07 | S10-S11, S24-S25 | Palace hall: the king on a raised seat, nobles kneeling, a commander kneeling to receive a gold-handled sword |
| K08 | S12, S38 | Night: soldiers with torches and ladders storming a hilltop fort above the river; a red banner over the fort at dawn |
| K09 | S13-S14, S36 | A Rajput prince on a white horse riding into a big camp of green tents and horse lines, forest hills behind |
| K10 | S16, S19 | Workers raising a long earthen wall with a bamboo palisade between two green hills by the river |
| K11 | S18 | Torchlight on an unfinished stretch of wall; a commander facing an officer, sword raised (no strike) |
| K12 | S20-S21 | Open plain: a white-and-red infantry line, a saffron cavalry charge coming at it, dust |
| K13 | S22-S23 | Night camp: raiders slipping out of the trees; an arrow with a rolled letter stuck in a post by a fire |
| K14 | S32, S34-S35 | From above: small boats lashed into a bridge across the narrows, big boats caught between them, smoke |
| K15 | S33 | A big Mughal war boat: the admiral seated on a carpet with a hookah, cannon along the side |
| K16 | S39 | Present day, dawn: a tall statue of a warrior standing in the river at Guwahati, a ferry passing |
| K17 | S42, thumbnail | The narrows at dusk, one small boat at the bank under the hill, torches |
| T1 | thumbnail | High angle on the narrows at dusk: a wall of big boats with cannon smoke bottom left, one small boat top right with a pale, wrapped figure at the prow, torchlit. Orange fire against a teal river. Space top left for title text |

## Beat table

| Beat | Starts | Length | Set | Join | Picture (time events to the words) | Camera | Ref |
|---|---|---|---|---|---|---|---|
| S01 | 0:00 | 18 s | A, late afternoon | open | **0:00:** close on Lachit on a mat under a thatched shelter on Itakhuli hill, pale, sweating, attendants beside him. Pull back past him over the hill edge to the river: small Ahom boats turning upstream, and the big Mughal fleet with cannon smoke coming on from downstream | pull back and rise from Lachit to the river | K01 |
| S02 | 0:17 | 13 s | A | continuous | Down to the bank under the hill: six or seven small boats still there, rowers waiting; the big fleet grows behind them on 'against an empire' | descend to the bank, low over the water | K02 |
| S03 | 0:30 | 18 s | B | cut (after the title card) | Parchment map of the valley, north up. On 'Guwahati' the hill cluster that pinches the river; on 'Lachit' a red figure token there; on 'Aurangzeb' a green fleet token downstream | top-down, slow push in toward Guwahati | K03 |
| S04 | 0:48 | 17 s | B | continuous | Green horsemen blocks gather in the west (the 18,000 horsemen). On 'took its capital' a green arrow sweeps up the valley to the palace in the east, then fades | glide east along the river and back | K03 |
| S05 | 1:05 | 21 s | A | cloud dissolve | Down from the map into the narrows: hills on both banks press in, the river barely a kilometre wide; on 'a defeat' the light dims | descend into the narrows and fly downstream low over the water | K04 |
| S06 | 1:27 | 23 s | B | cut | The whole valley from above: forest and hills as 3D props; Ahom land washes red; the capital Garhgaon in the east; a blank-paged chronicle book (no text) on 'Buranjis' | top-down glide east along the valley | K03 |
| S07 | 1:49 | 21 s | B | continuous | Green spreads over the west (Mughal India). On 'Mir Jumla' a long green column of troop blocks and boats starts up the river | follow the column east | K05 |
| S08 | 2:10 | 17 s | C | dissolve | Garhgaon: green-bannered soldiers at the palace gate; the royal party leaves by the forest road into the hills; rain sweeps in, Mughal tents sag and soldiers huddle | descend to the gate, pan to the hill road as the rain starts | K06 |
| S09 | 2:27 | 17 s | B | dissolve | Map: a closed palanquin, a line of four young hostages, chests and elephants move west along the river; on 'Guwahati' the red there turns green | rise to the map and follow the line west | K05 |
| S10 | 2:44 | 17 s | D | cut | Palace hall: King Chakradhwaj on his raised seat; nobles kneel and plead; the king stands. On 'Meet Lachit' Lachit steps forward from the side | push in down the hall | K07 |
| S11 | 3:02 | 21 s | D | continuous | The king hands Lachit the gold-handled hengdang; Lachit kneels to take it | slow orbit around the two | K07 |
| S12 | 3:22 | 16 s | A, night to dawn | cut | Itakhuli hill at night: Ahom soldiers climb with torches and ladders to the Mughal fort; at dawn a red banner rises over the fort; on 'Aurangzeb' the camera turns west down the river | track up the hill with the climbers, rise to the banner, turn west | K08 |
| S13 | 3:39 | 16 s | F | cut | Ram Singh rides a white horse into a big camp of green tents; Rajput horsemen behind him | track alongside Ram Singh | K09 |
| S14 | 3:55 | 21 s | F, dusk | continuous | Inside his tent: Ram Singh alone at a low desk, head down. The camera drifts to the tent door: rain, dense forest, mist on the hills | slow drift from Ram Singh to the doorway | K09 |
| S15 | 4:17 | 23 s | B | dissolve | Map: the army moves east along the river (horse, foot, archers, cannon, a fleet of war boats). A separate small camp far behind at Dhubri, tents only, **no figure of the Guru** | follow the column east | K05 |
| S16 | 4:39 | 19 s | A | cut | The Guwahati hills from above; Ahom workers pile earthen ramparts between the hills; the camera traces the wall line | glide along the rampart line | K10 |
| S17 | 4:58 | 20 s | A | continuous | Down to the narrows: big Mughal boats with rows of cannon on one side, small fast Ahom boats with rowers on the other; on 'barely one kilometre' fly across the width | fly across the river at low height | K04 |
| S18 | 5:18 | 15 s | A, night | continuous | Torchlight on an unfinished stretch of wall; Lachit faces an older officer; Lachit's sword rises and the camera turns away to the wall | slow push in, then swing away | K11 |
| S19 | 5:33 | 15 s | A, dawn | continuous | Morning: the wall finished, workers resting along it | rise along the finished wall | K10 |
| S20 | 5:48 | 13 s | G | cut | Alaboi plain: the Ahom infantry line in the open under the king's banner; Lachit stands apart, arguing, then turns away | track along the Ahom line | K12 |
| S21 | 6:01 | 16 s | G | continuous | Rajput cavalry charges through the line; dust; fallen red banners (no gore); Lachit's head bowed | rise and pull back over the plain | K12 |
| S22 | 6:17 | 15 s | F, night | cut | Mughal camp at night: Ahom raiders slip out of the forest, set a tent alight and vanish into the hills | track the raiders from the tree line | K13 |
| S23 | 6:33 | 15 s | H (A at night) | continuous | Ahom camp under the hill: an arrow thuds into a post by a fire; a rolled letter is tied to it (blank) | follow the arrow in | K13 |
| S24 | 6:48 | 17 s | D | cut | Court: the king holds the blank letter, frowning; Atan Burhagohain speaks at his side; the king nods | slow orbit | K07 |
| S25 | 7:05 | 22 s | D | continuous | The council: a ring of nobles, most nodding; Atan alone stands and shakes his head; the new king listens (Udayaditya on the seat) | slow push in on Atan | K07 |
| S26 | 7:28 | 17 s | A | cut | March 1671: the Mughal army marches along the north bank; a new fleet with green flags comes up toward the narrows; low cloud | wide glide from downstream to the narrows | K04 |
| S27 | 7:44 | 18 s | A | continuous | Lachit on his mat at Itakhuli. Below, on the north bank, Ahom soldiers drive Mughals back; on the water, the Ahom boats are pushed back | rise from Lachit to the river | K01 |
| S28 | 8:03 | 12 s | A | continuous | Ahom boats slip away upstream; Lachit raises himself on one arm to watch | push in on Lachit, then turn to look where he looks | K01 |
| S29 | 8:15 | 17 s | A | continuous | Close on Lachit, the narrows behind him, the fleet coming; low light | slow orbit around Lachit | K01 |
| S30 | 8:32 | 15 s | A | continuous | Lachit is helped down the hill path to the bank and into a boat; six or seven boats push off | track with him down to the water | K02 |
| S31 | 8:47 | 17 s | A | continuous | Lachit stands in the prow with the rowers around him; the boats head for the fleet | low over the water behind his boat | K02 |
| S32 | 9:04 | 20 s | A | continuous | Ahom boats turn back and gather; they lash together into a bridge across the river; the Mughal fleet is caught between attacks front and rear | rise high to watch the bridge form | K14 |
| S33 | 9:24 | 15 s | A | continuous | The admiral's big boat: Munawwar Khan on a carpet with a hookah; a musket flash; he slumps (no gore) | push in on the admiral's boat | K15 |
| S34 | 9:39 | 12 s | A | continuous | The Mughal fleet breaks and turns downstream; drifting boats, smoke over the water | pull back high | K14 |
| S35 | 9:51 | 14 s | A | continuous | Ahom boats stop at the narrows; Lachit raises a hand to hold them; the Mughal boats far downstream. On 'Ram Singh withdraws' a long view west | hold on Lachit's boat, slow rise | K14 |
| S36 | 10:05 | 19 s | F | cut | The Mughal camp being struck at the frontier; Ram Singh by his horse, looking back east | slow push in on Ram Singh | K09 |
| S37 | 10:23 | 20 s | B | cut | Map: a small royal burial mound near Jorhat in the east on 'April 1672'; on 'his own brother' the red at Guwahati turns green | top-down glide west from Jorhat to Guwahati | K05 |
| S38 | 10:44 | 20 s | A | dissolve | Itakhuli fort: red banners rise again; the camera lifts until the whole valley reads red | rise from the fort to a very high view | K08 |
| S39 | 11:04 | 21 s | A, today | dissolve | Present-day dawn at Guwahati: the tall Lachit statue standing in the river, a ferry passing, calm water | slow glide toward the statue | K16 |
| S40 | 11:25 | 19 s | A | dissolve | Late golden light over the narrows: ramparts, hills, small boats; each cause in the line gets its picture (hills, small boats, the council hall far off) | wide slow orbit | K04 |
| S41 | 11:44 | 21 s | A | continuous | The orbit comes to the spot where the boat bridge stood; the river empty and calm | continue the orbit, descend toward the water | K04 |
| S42 | 12:05 | 10 s | A, dusk | continuous | Echo of the hook: the narrows at dusk, one small boat at the bank under Itakhuli hill, torches, no fleet | slow rise; hold into the end screen | K17 |
| End | 12:15 | 18 s | (last set) | continuous | Silent hold and slow fade under the YouTube end screen (or the next-video line once that video exists) | continue the last move | - |

## Shorts to cut (vertical, 30-50 s, each with its own hook line and a link to the full video)
1. **"My uncle is not greater than my country"** (S16-S19): the wall, the torchlight, the proverb, labelled as tradition.
2. **The sick commander** (S27-S33): the fleet running, Lachit climbs into a boat, the boat bridge.

## Order of work
1. Characters and the 17 keyframe stills plus the thumbnail still in Flow (free). Get the user's approval of all of them.
2. Build the shared kit parts (list above), then set A (biggest, most beats), then B (map), then C, D, F, G.
3. Record the voice from `audio/lines.txt` in story order (about 5 days at 10 requests a day on one key).
4. Build and review beat by beat in story order, as in `Blender_Build_Rules.md`.
