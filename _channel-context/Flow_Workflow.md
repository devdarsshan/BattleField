# Making a video with Flow MCP

Flow MCP is installed at `C:\Users\sdevdarsshan\flow-mcp` and is connected to Claude Code (the Code tab).
Output files land in `~/flow-mcp-out/<project>/`. Copy the finished ones into the battle's folder here.

## Order of work
1. **Check.** Run `flow_status` to confirm sign-in, the open project and the credits left. Tell the user the balance.
2. **Characters (free).** Use `flow_character` for each main person in the battle's shot list. Show the portraits and edit them with `flow_character_edit` until the user approves.
3. **Keyframe stills (free).** Describe each keyframe in words first and wait for an OK. Then generate it as an image (`flow_generate`, image) or in bulk (`flow_agent_images`). Fix any that look wrong. No video until every keyframe is approved.
4. **Clips (cost credits).** Use `flow_generate` for video at 720p, 10 seconds, `max_credits` 15. Read Flow's price quote first and tell the user. Default to 3 clips a day (45 of the free 50 credits) unless the user says otherwise.
5. **Narration (free).** Use `flow_narrate` with engine `gemini` (a key is stored in `~/.flow-mcp/gemini-key`; if it is missing, use the Windows voices) and a style note like: "Calm, clear documentary narrator, unhurried, short pauses between sentences."
6. **Cut (free).** Run `flow_assemble` with the clips in order and the narration on top. The footage must be at least as long as the narration, so the last frame never freezes.

## No-cut continuity (the channel rule)
- Every clip starts on the **real last frame** of the clip before it (`chain_previous`). This is the "exact join".
- Use the next approved keyframe as `last_frame` when a clip is meant to land on it.
- When a character appears for the first time, use `flow_continue`. It keeps the start frame and attaches the saved character.
- Before each new clip, check the last frame of the previous one: main faces should be visible and reasonably large. If not, regenerate that clip before moving on.
- To change location, never cut. Rise to map height, glide, and descend.

## Money rules
- Never generate video without the user's OK.
- Never regenerate something that already finished. Use `flow_download` to fetch it again for free.
- Avoid `flow_edit` (restyle) unless asked. It costs about 40 credits per edit.
