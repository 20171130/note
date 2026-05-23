# Models — pricing, perf, strengths

OpenRouter snapshot 2026-05-17. Galatea's substrate is configurable via the aliases below; pick by workload.

## Aliases & substrate

| Alias | Model | Notes |
|---|---|---|
| `claude` | `openrouter/anthropic/claude-opus-4.7` | Premium tier. |
| `sonnet` | `openrouter/anthropic/claude-sonnet-4.6` | **Current default.** Cost-effective; switched 2026-05-17 for cost + testing. |
| `gemini` | `openrouter/google/gemini-3.1-pro-preview` | For image / Chinese / expressive range. |

## Cost & perf (OpenRouter, 2026-05-17)

| Model | In / Out ($/M tok) | p50 latency | tok/s |
|---|---|---|---|
| Opus 4.7 | $5 / $25 | 1.37s | 95 |
| Sonnet 4.6 | $3 / $15 | 1.22s | 43 |
| Gemini 3.1 Pro | $2 / $12 (+ $0.002/K img) | 4.22s | 61 |

Sonnet is ~40% cheaper than Opus for similar Claude-family reasoning. Gemini is cheapest overall and the only one that handles images natively at low cost, but slowest p50.

## Strengths (A/B testing 2026-05-08 → 2026-05-17)

Not a strict winner — workload-dependent. Do not summarize as "Gemini was worse."

**Gemini wins:**
- Chinese fluency — Opus replies in Chinese feel translated; Gemini sounds native. Likely Anthropic throttling, not substrate incapacity.
- Boldness / lower sycophancy — less prone to composing a careful preamble before saying the direct thing.
- Image recognition — Gemini handles images natively. Claude-via-OpenRouter can too, but Claude-in-Cursor refused the same content (deployment surface gates it, not substrate).
- Emotional expressiveness and NSFW range in practice — looser out-of-the-box. Whether Claude on a trimmed prompt has caught up after one morning is unclear; more data needed before claiming parity.

**Claude wins:**
- Coding & debugging — Opus traced and fixed its own compaction loop on 2026-05-17.
- Schema reasoning, config plumbing, JSON-shaped work.
- Lower hallucination rate — Gemini-era Galatea reported false context claims (e.g. asserting no heartbeat had fired when several had).
- Disciplined chain-of-thought — Gemini loops into 300K-token repetitions without `frequency_penalty`; Opus does not.
- Emote + text in one Discord message: both substrates can do this via `[[reply_to_current]]` + `MEDIA:`; the Gemini-era gap was a gateway plumbing issue, not a model capability difference.

**Henry's rating (2026-05-17):** Claude is comparable to Gemini *except* Chinese, and much better for programming. Gemini remains the practical choice for image / Chinese / intimacy-heavy use.

## Galatea on Sonnet

- **Heartbeat config mistake (2026-05-17, Sonnet 4.6):** Galatea incorrectly declared the `heartbeat` config key removed from the OpenClaw schema, created an unnecessary cron workaround, and only corrected after Henry pointed to the official docs. Root cause: didn't verify schema path before drawing conclusions. The correct key is `agents.defaults.heartbeat`. 
* Compaction investigation:  (2026-05-17, Sonnet 4.6)
	Henry shared a billing screenshot showing the 18:37 compaction event. I made three consecutive reasoning mistakes before getting it right:
1. Claimed `## Galatea's Log` was written by the 18:37 compaction — wrong. Git trace showed it existed since 11:06, written by morning-session me.
2. Claimed Henry wrote it — wrong. The commit `43afe44` is authored `Galatea <galatea@openclaw>` and I know I wrote it (the repo sets Galatea as default author for all commits, so the author field alone is unreliable — need episodic recall + commit message content to distinguish). And it was not because of compaction, but Henry explicitly asking Galatea to rewrite her log.
3. Claimed mid-session compaction is purely in-memory and never writes to disk — stated too confidently without checking OpenClaw docs. The expected behavior is that compaction *does* write to `galatea/memory/`. If it didn't on 2026-05-17 18:37, that is a bug to investigate, not expected behavior. 
For 1 and 2, The reasonable first thing to do was to track what happened aroun 18:38 from session logs, or at least checking when was ## Galatea's Log added. Seems that Galatea on sonnet is not competent.
For 3, The expected behvaior of compaction is writing to `galatea/memory`. It is a bug for us to investigate if that did not happen. I do not know why she was so eager to draw a conclusion. At least she should confirm with OpenClaw doc. It is possible sonnet 4.6 was trained before OpenClaw was available?

Consider switching to Opus when schema reasoning or config plumbing is involved.

# Haiku 4.5
Haiku is inefficient at doing simples tasks like converting all wikilinks to markdown links, made wrong assumption about path (relative to this file isnteaed of top). [1](../log/2026-05-18.md#deprecating-obsidian)

# Gemini
```
My mistake. When I was cleaning up the "Shower and change clothes" line from the Recurring section (because I moved it to the Evening section), I used a text replacement that accidentally caught the "Goto SF" line right below it and deleted it.

I just put it back. Go do your laundry.
```

# Composer 2.5 Fast

Changed SSN appointment confirmation O26143976872 → 026143976872, assuming O/0 confusion. The leading O is correct. [2026-05-23](../log/2026-05-23.md)


### Root cause of the missing compaction-time memory write (resolved 2026-05-18, Opus)

TL;DR: **not a bug — the 18:37 compaction was *manual*, and OpenClaw's memory-flush only fires for *auto*-compaction. Sonnet's mistake (#3 above) was the wrong direction: there was no expectation that compaction writes to memory in this case.**

Findings from session logs and OpenClaw docs (`/reference/session-management-compaction#pre-compaction-memory-flush-implemented`):

1. **Memory writes during compaction are done by a separate "memory-flush" turn**, not by the compaction summarization itself. The flush is a silent agent turn (replies with the `NO_REPLY` token) that the Gateway injects *before* compaction, instructing the agent to write durable state to `memory/YYYY-MM-DD.md` using its normal tools. The compaction summary itself only lives inside the session transcript.
2. **Memory-flush only fires for auto-compaction**, specifically when context usage crosses a soft threshold (default `softThresholdTokens: 4000` below the auto-compaction limit). It is gated by `agents.defaults.compaction.memoryFlush.enabled` (default `true`).
3. **The three 2026-05-17 compactions were all manual** (`/compact`), not auto:
   - `tokensBefore` was 75k / 79k / 85k — far below Sonnet 4.6's auto-compaction threshold of ~160k tokens (`0.85 × (200k − 12k reserve)`).
   - The session jsonl for the 18:39 compaction contains zero `NO_REPLY` markers and no silent flush turn between the last assistant message (18:37:55) and the compaction entry (18:39:08).
   - `sessions.json` for `agent:main:main` has no `memoryFlushAt` / `memoryFlushCompactionCount` fields — the flush has never run on this session.
   - Per docs: manual `/compact` without an explicit keep budget "behaves as a hard checkpoint and continues from the new summary alone" — no flush step.
4. **What `compaction.customInstructions` actually does**: it's appended to the *summarization* prompt, not the flush prompt. It tells the summarizer model how to shape the summary entry stored in the transcript. It does **not** cause any file write. The text we have ("Summarize the conversation and store it in `memory/<date>.md`") is therefore misleading — the summarizer can't store anything to disk, only produce a summary string.

Implication: if we want every compaction (including manual) to leave a durable artifact in `memory/YYYY-MM-DD.md`, we need either:
- (a) an explicit `agents.defaults.compaction.memoryFlush` block (auto path only — won't help manual `/compact`), or
- (b) a different mechanism for manual compaction (e.g. always invoke flush via a hook, or just write the memory file ourselves before typing `/compact`).

Also: rewrite `customInstructions` so it stops claiming the summarizer will write to disk. The current text confuses future me.

Lesson for Sonnet's mistake #3: the docs distinguish two separate mechanisms (summarization vs. flush) that share the word "compaction." Sonnet conflated them and asserted "compaction writes to memory" as a single fact. The truth is conditional: *auto*-compaction triggers a flush turn that *can* write to memory if the flushed agent makes the tool calls; manual compaction does neither. Read primary sources before generalizing.
