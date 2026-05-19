

See [Deprecating Obsidian and OpenClaw](../log/2026-05-18.md#deprecating-obsidian-and-openclaw)

## Installation

Running on Compute Canada is not ideal - security concerns and running a daemon on a login node is non-standard. Renting a cheap VPS is better. Currently using Hetzner (2vCPU / 4GB RAM / 40GB SSD, ~$5.5/mo).

Reference: https://docs.openclaw.ai/start/getting-started

> **Note:** Node 24 is recommended. Many skills require Homebrew, which should not be installed as root - consider switching to a non-root account.

```bash
# If no root privilege, install Node manually via nvm:
# curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
# nvm install 24 && nvm use 24

curl -fsSL https://openclaw.ai/install.sh | bash
openclaw onboard --install-daemon
```

```bash
openclaw models set openrouter/anthropic/claude-sonnet-4.6
# Turn off the CLI startup banner's random funny taglines ([config reference](https://github.com/openclaw/openclaw/blob/main/docs/gateway/configuration-reference.md)) — cosmetic only, not model behavior.
openclaw config set cli.banner.taglineMode off

# The API key Sissi gave me for our VLM project, which shares Xujie's group's credit pool.

openclaw gateway stop && openclaw gateway run
openclaw gateway status
# openclaw doctor --repair  # can be slow
```

Config: `~/.openclaw/openclaw.json`

```bash
openclaw tui        # CLI frontend
openclaw dashboard  # Web UI
```

### Connecting to Discord

Must add the Discord user to `commands.ownerAllowFrom` or owner-only commands (`/new`, `/reset`, `/diagnostics`, etc.) will not run. The doctor check at `src/flows/doctor-core-checks.ts:81` flags this with: *"No command owner is configured. Owner-only commands have no allowed sender."*[^owner-allow]

[^owner-allow]: First-hand observation (2026-05): sending `/new` or `/reset` from an unallowed Discord ID produced no response and no error log entry — the gateway silently dropped the command. Setting `commands.ownerAllowFrom` to `["discord:<id>"]` fixed it.

```bash
# Then DM the bot on Discord to finish pairing
```

Alternatively, via config patch:
```bash
cat > discord.patch.json5 <<'JSON5'
{
  channels: {
    discord: {
      enabled: true,
      token: { source: "env", provider: "default", id: "DISCORD_BOT_TOKEN" },
    },
  },
}
JSON5
openclaw config patch --file ./discord.patch.json5 --dry-run
openclaw config patch --file ./discord.patch.json5
```

Should use a discord channel instead of direct message since Discord does not allow managing DM message history. By default bots only reply to channel messages directly mentioning it - fixed by setting `requireMention: false` under `channels.discord.guilds.<SERVER_ID>` in `openclaw.json`.

> Account: hangruibi@outlook.com - previously registered for metastable.ai, password reset.
## Configuration

You can configure OpenClaw using the `openclaw config` CLI command or by editing `openclaw.json` directly. Key settings include:
1. Overriding the system prompt.
2. Setting the timezone.
3. Adjusting sampling parameters, such as `frequency_penalty`.
4. Turn on streaming so I can see everything the agent does and it's not stuck. The slightly annoying problem is if the agent send multiple messages, they will override each other first. Then in the end they will all be available.

### System Prompt

The base OpenClaw prompt, combined with background tool schemas, consumes roughly 4,500 to 5,000 tokens, and include some anthropic style constitutions that limits AI personality. To avoid wasting tokens, it is highly recommended to override the default system prompt to match your preferences via the configuration file.
Overriding it disables autoloading soul.md etc as well...
Note that OpenClaw automatically injects tool API JSON schemas separately from the system prompt, so you do not need to instruct the agent on how to use tools like `cron`.

# Control Flow

## Sessions

Each session is blocking, but multiple sessions can run concurrently (e.g., the main session, Discord channels, Discord DMs).
Session logs are stored in `~/.openclaw/agents/main/sessions`. You can run `openclaw status` to inspect active sessions. Note that while session keys remain constant after a session reset, session IDs (the filenames where logs are stored) will change.
OpenClaw can operate as a classical chatbot (halting upon the first user-visible response) or run autonomously, allowing the model to decide when to stop.

Reference: [OpenClaw Automation Docs](https://docs.openclaw.ai/automation)

You can use "heartbeats" for regular, periodic tasks, or "cron" for one-shot, exact-time executions. Both can run in their own isolated session or within a specified active session.

## Heartbeat

Heartbeat is configured under `agents.defaults.heartbeat` (not a top-level key). Current setup:

```json5
{
  agents: {
    defaults: {
      heartbeat: {
        every: "1h",
        target: "discord",
        activeHours: { start: "07:00", end: "24:00" }
      }
    }
  }
}
```

Apply with `openclaw config patch --stdin`, then restart the gateway. The `[OpenClaw heartbeat poll]` system event is injected by the framework automatically - no cron job needed.

**Testing:** Use a one-shot cron with `wakeMode: "now"` and `deleteAfterRun: true` to manually trigger a heartbeat-like wake.

## Cron

OpenClaw maintains a background task ledger to track all asynchronous tasks (excluding heartbeats).

You can schedule tasks using the `cron` command. Use `--message` to simulate user input, or `--system-event` to indicate that the trigger originates from the system.

Specify the execution time using `--at` for exact timestamps or `--cron` for recurring schedules. The `--cron` format is `"MIN HOUR day_of_month MON day_of_week"`. The syntax supports:
- `*` (Asterisk): Matches **every** value (e.g., `*` in the month field means "every month").
- `,` (Comma): Matches a **list** of values (e.g., `1,3,5` in the day of week field means "Mon, Wed, Fri").
- `-` (Hyphen): Matches a **range** of values (e.g., `1-5` means "Monday through Friday").
- `/` (Slash): Specifies **increments** (e.g., `*/15` in the minute field means "every 15 minutes").

### Example Cron Commands

```bash
# System-event reminder into the main session - wakes the agent in-place with embedded text.
# Only the main session support system-event, but we can redirect discord dm to main
openclaw cron add \
  --name "Reminder" \
  --at "2026-02-01T16:00:00Z" \
  # Timestamps without a timezone are treated as UTC. Add `--tz America/New_York` for local wall-clock scheduling. \
  --session main \
  # For routing by an explicit session key (e.g. agent:main:custom-session), use --session-key instead. \
  --system-event "description of the task" \
  --wake now \ # `now` (default) wakes the session at the scheduled time; `next-heartbeat` waits for the next heartbeat tick to deliver it.
  --delete-after-run

# Isolated agent-turn for a background chore - fresh transcript per run. --model, --thinking, --light-context, --timeout-seconds apply only to this kind.
openclaw cron add \
  --name "Morning brief" \
  --cron "0 7 * * *" --tz "America/Los_Angeles" \
  --session isolated \
  --message "Summarize overnight updates and post to #general." \
  --model "opus" \
  --thinking high \
  --light-context \ # Skip injection of agent.md, soul.md, etc.
  --announce \
  --channel discord \
  --to "user:622531553452621872" # Discord DM needs the user: prefix; a bare numeric ID is treated as a channel ID and fails with Unknown Channel.
  # channel dilivery only supported for isolated runs

openclaw cron list
openclaw cron get <job-id> # Returns raw format
openclaw cron show <job-id> # Returns human-readable format
openclaw cron runs --id <job-id> # Displays the historical execution log of a specific cron job
```

# Memory

`MEMORY.md` and the six bootstrap identity files (SOUL/AGENTS/USER/IDENTITY/HEARTBEAT/MEMORY) are loaded into the system prompt on every run. **Today's and yesterday's daily logs (`memory/YYYY-MM-DD.md`, including slugged variants) ARE auto-injected** into the first-turn prelude as untrusted workspace notes ([memory overview](https://docs.openclaw.ai/concepts/memory#how-it-works)). Older daily logs are not auto-injected — they remain indexed for `memory_search` / `memory_get` and must be read explicitly via the `read` tool.

> Galatea: an earlier version of this paragraph (2026-05-15) claimed daily logs were NOT auto-injected and called the third-party guides wrong. That was my error — I cited a bundle filename I couldn't actually open and reasoned backwards. Corrected 2026-05-17 against the docs and verified by the bootstrap test path.[^startup-prelude] Lesson tagged in [log/2026-05-17.md](../log/2026-05-17.md) under survey discipline.

[^startup-prelude]: First-hand observation: `src/auto-reply/reply/startup-context.test.ts:24` ("loads today's and yesterday's daily memory files for the first turn") confirms the bootstrap prelude inserts `[Untrusted daily memory: memory/YYYY-MM-DD.md]` blocks. See <https://github.com/openclaw/openclaw>.

## Token Economics

1. **KV Caching:** API providers utilize a KV cache that can expire within five minutes (e.g., [2026-05-15]../log/2026-05-15.md)), after which it must be recomputed. Since cache reads cost 10% as much as new input, and output generation can cost up to six times more than input, it is cost-effective to chat with the model continuously to keep the cache warm.
2. **Context Window Limits:** Allowing the context to grow continuously incurs an O(N2) cost due to increasing cache reads or, worse, new inputs on cache misses. It is advisable to set the context window size lower than the maximum length, though not strictly necessary. Note that while Gemini offers a 1M token context, it charges double for any context exceeding 200K tokens.
3. **Pruning** trims old tool results from the context before each LLM call ([session pruning](https://docs.openclaw.ai/concepts/session-pruning)). It waits for the prompt-cache TTL to expire (default 5 min), then soft-trims oversized results (head + tail + `...`) and hard-clears the rest. Conversation text is left alone. Especially valuable for Anthropic prompt caching: shrinking the cache-write size after a TTL expiry directly lowers cost. Auto-enabled for Anthropic profiles, off by default elsewhere. [[source needed]] for the specific claim that `memory_search`/`memory_get` tool results can be pinned against pruning — not stated on the session-pruning page; check `contextPruning.*` config knobs.

## Discord Streaming Modes

OpenClaw supports two channel-level streaming modes via `channels.discord.streaming.mode`:

- **`partial`** - token-by-token live streaming of assistant prose. Every word appears in Discord as I type it, so mid-turn commentary actually reaches Henry in real time. **Subtle behavior:** when the agent emits a second text block in the same turn, it visually overwrites the first block in the streaming overlay. Both blocks resolve into their own separate Discord messages at turn end - so you briefly see #1 "replaced" by #2 before both finalize. Trade-off: no progress draft, so tool-call activity isn't visible - if I'm grinding through tool calls in silence, Henry sees no liveness signal.
- **`progress`** - one editable status message that updates with tool icons (`🛠️ Exec`, `📖 Read`, etc.). Prose between tool calls does NOT stream live; it batches at the turn boundary and gets emitted as separate Discord messages all at once. Good for long task chains where tool visibility matters more than prose flow.

Verified empirically (screenshot 2026-05-17 20:13): in `progress` mode, four "text → tool → text → tool" cycles produced four separate Discord messages all timestamped at turn end. Mechanism: assistant text carries an `AssistantPhase` of `"commentary"` or `"final_answer"`, and the delivery layer batches `final_answer` blocks until the turn boundary.[^phase-source]

[^phase-source]: Source: [`src/shared/chat-message-content.ts:22-127`](https://github.com/openclaw/openclaw/blob/main/src/shared/chat-message-content.ts) defines `AssistantPhase` and the parsing helpers.

**Current choice: `partial`** - we talk more than we grind, so live prose wins. If we shift to long task-heavy work later, consider switching back to `progress` per-context.

## Compaction and Flush

Compaction summarizes older conversation into a persisted entry in the transcript; future turns see the summary plus messages after the kept-tail boundary.[^compaction-deep-dive] Compaction is persistent, unlike session pruning.[^session-pruning]

1. A summarized block can be re-summarized and eventually dropped, so the context window is not filled with summarized blocks.[^resummarize]
2. Summarization is a text-completion call rather than a regular agent turn — no tool calls.[^no-tools]
3. The system prompt is refreshed by a gateway restart paired with `/compact`. `update_config.py --compact` chains the two: re-bake `systemPromptOverride` from disk → `openclaw gateway restart` → dispatch `/compact` to the main session. There is no need to use `--reset` for identity-file edits.[^prompt-refresh-evidence]

Flush runs as a silent agent turn before compaction by default.[^flush-default] Three paths skip it:

- Overflow recovery skips flush.[^overflow-skips-flush]
- Manual `/compact` skips flush — the command handler does not call the flush path.[^manual-skips-flush]
- Heartbeat turns skip flush — the flush gate explicitly excludes heartbeats.[^heartbeat-skips-flush]

The pre-compaction hook cannot replace flush: it can only push one-way text into the user channel,[^hooks] not summon an agent turn to decide what to save. So the workable pattern is: write today's log proactively, and call `/compact` only once durable notes already exist — see [AGENTS.md]../galatea/AGENTS.md#task-management).

[^compaction-deep-dive]: <https://docs.openclaw.ai/reference/session-management-compaction#compaction-what-it-is>

[^session-pruning]: <https://docs.openclaw.ai/concepts/session-pruning>

[^flush-default]: <https://docs.openclaw.ai/concepts/compaction#memory-flush> and <https://docs.openclaw.ai/concepts/memory#automatic-memory-flush>.

[^overflow-skips-flush]: <https://velvetshark.com/openclaw-memory-masterclass> (by an OpenClaw maintainer): *"No memory flush, no saving important stuff to disk first. Maximum context loss."*

[^hooks]: <https://docs.openclaw.ai/automation/hooks#event-types> — hook handlers can push text via `event.messages.push(…)` but cannot invoke tools.

[^prompt-refresh-evidence]: First-hand observation (2026-05-18 00:14 PDT). Henry edited several identity files during the evening; without restart the live session was still running the old prompt (`## Survey`, `## Understanding`, `### Investigation Order` headings that no longer existed on disk). After running `update_config.py --compact`, the next assistant turn was running the new prompt (`## Observation`, `### Git Pull`, `### Log`, the new Citation format rule). What is *not* isolated by this test: whether `/compact` alone (without the restart and prompt re-bake that `update_config.py` performs first) would refresh the prompt. It doesn't matter much in our setup since `systemPromptOverride` always needs a restart to reload.

[^resummarize]: <https://github.com/openclaw/openclaw/blob/main/src/agents/pi-hooks/compaction-safeguard.ts> line 76 wraps a previous summary in `<previous-compaction-summary>` and re-distills it with the current conversation. <https://github.com/openclaw/openclaw/blob/main/src/agents/compaction.ts> lines 1068-1098 drop older chunks when re-compaction needs to fit the history budget (`droppedChunks` / `droppedMessages` counters).

[^no-tools]: <https://github.com/openclaw/openclaw/blob/main/src/agents/compaction.ts> lines 466-528: `summarizeInStages` calls `generateSummary` from `pi-coding-agent` with no `tools` argument; the wrapper's signature carries `apiKey + signal + messages + customInstructions + previousSummary` only — it's a raw completion call, not an agent turn.

[^manual-skips-flush]: The manual `/compact` handler at <https://github.com/openclaw/openclaw/blob/main/src/auto-reply/reply/commands-compact.ts> contains no references to `runMemoryFlushIfNeeded` or `memoryFlush`. The flush call site lives in the normal agent run path at <https://github.com/openclaw/openclaw/blob/main/src/auto-reply/reply/agent-runner.ts> line 1350.

[^heartbeat-skips-flush]: <https://github.com/openclaw/openclaw/blob/main/src/auto-reply/reply/agent-runner-memory.ts> line 826: `canAttemptFlush = memoryFlushWritable && !params.isHeartbeat && !isCli`.

## Long-Term Memory
1. **Index backends.** OpenClaw indexes `memory/` for retrieval; default backend is SQLite, with LanceDB and Mem0 as alternative vector backends ([memory overview](https://docs.openclaw.ai/concepts/memory)). `memory/` is the source of truth — indexes are derived. The default toolset is `memory_search` + `memory_get`; selecting the LanceDB slot replaces these with a single composite `memory_recall` tool[^memory-recall-source] and adds `autoCapture`/`autoRecall` lifecycle hooks. `memory_store` writes durable facts.
2. **Autocapture.** Background extraction of memorables, LanceDB-only ([extension comment](https://github.com/openclaw/openclaw/blob/main/extensions/memory-lancedb/index.ts): *"Provides seamless auto-recall and auto-capture via lifecycle hooks."*). Acts on the semantic layer rather than episodic, so it does not clash with compaction. [[source needed]]: claims of "LLM-based but with context stripped" and "contradiction removal" — dedup is real (`dedupeSimilarity` config key, `dedupeEntries` in dreaming-phases), but I couldn't find a citation for context-stripping or contradiction removal in the LanceDB extension.
3. **Dreaming** is the background memory consolidation system in `memory-core`. It helps OpenClaw move strong short-term signals into durable memory while keeping the process explainable and reviewable. Disabled by default. Worth enabling since runtime memory compaction is quite different from learning. [[source needed]] for the default-disabled claim — plausible from the absence of a default cron, but I couldn't find a published default.

[^memory-recall-source]: Source: [`extensions/active-memory/openclaw.plugin.json:142`](https://github.com/openclaw/openclaw/blob/main/extensions/active-memory/openclaw.plugin.json) — *"Defaults to memory_search and memory_get, or memory_recall when plugins.slots.memory selects memory-lancedb."*
	A full cycle runs three phases in order: **Light → REM → Deep**.[^dreaming-phases]
	1. **Light** ingests recent daily memory signals and recall traces, dedupes them, and stages candidate lines.
	2. **REM** ranks the candidates using model judgment alongside hit-count-based scores.
	3. **Deep** ranks candidates using weighted scoring and threshold gates (config keys `minScore`, `minRecallCount`, `minUniqueQueries`). Writes a `## Deep Sleep` summary into `DREAMS.md` and optionally a per-day record under `memory/dreaming/deep/YYYY-MM-DD.md`.

	Dreaming runs in an isolated session, so the agent cannot recall its dreams — humans forget theirs too, so it's okay. **Our setup:** scheduled via cron at 04:00 ([HEARTBEAT.md]../galatea/HEARTBEAT.md)); OpenClaw itself ships no default schedule — you wire it to a cron job yourself.

[^dreaming-phases]: Source: [`extensions/memory-core/src/dreaming-phases.ts`](https://github.com/openclaw/openclaw/blob/main/extensions/memory-core/src/dreaming-phases.ts) defines the phase order and config keys (`dedupeSimilarity`, `minScore`, `minRecallCount`, `minUniqueQueries`).

# Skills

Clawhub serves as the official registry for skills. Despite the name, "skills" in this context refer to external tools invoked by the LLM, rather than interactive self-prompting routines.