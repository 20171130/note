
I classify software into four categories, according to how human interacts with them, and the degree of automation / the amount of input needed:

- **Copilot / IDE** - thinking, writing, development, deep work
- **CLI** - like Claude Code, more autonomous paradigm then Copilot
- **Daemon** - like OpenClaw with heartbeats, push and auto-recommendation, almost zero input
- **Proxy** facing other humans as a surrogate of the user, like OpenClaw via discord channel or reading/writing emails. It requires negative input in the sense that it reduces the information flux of the user

Although the later two may seem more exciting, the first two are used much more frequently. Chatting on Discord may feel good during the first two days, but for any deep work the information bottleneck is not tolerable, and I feel the need of copilot paradigm: writing the same file together.


My two needs emerged as I experimented with OpenClaw from 2026-05-08.
1. Task Mangement
2. Deep Work
For the first, heartbeat and cron is needed, maybe also discord notification and persistent session.
For the second, Cursor/Claude Code is good. How can I integrate them?

# Cursor
1. User level rules via Cursor setting.
2. Project and fine-grained: `.cursor/rules/.mdc` files (`.cursorrules` is legacy). placed at project root. Can set always apply/ match file path/ manual apply via @ and intelligent apply.
3. .cursor/skills/name/SKILL.md, invoked via /skill. I think they are quite similar to rules execpt for semantic flavor.
4. Rules can include other rules and skills, resursive include are handled gracefully (tested). But skills cannot inlcude other files. We can try to keep everything as rules, and use skills as command shortcuts or to keep scripts.

```markdown
---
description: Use when writing or modifying API routes
globs: src/pages/api/**/*.ts, src/app/api/**/*.ts
alwaysApply: false
---
# Your API rules go here...
```

## RAG

Cursor automatically indexes the whole code repo, AST chunking + vector indexing, neither adjustable or quite reliable.
The agent is given recently opened file names as context, or it can use grep to search. I found it recall memory via this more than semantic search.
Notice that the vector database is in cursor server, not local. Can check this via cursor settings -> doc and indexing.


## Example
[Mingdong Wu's Agent](../../reading/2026/wmd-agent.md)
Core design principles I found:
1. Lightweight boot + routing table
2. Identify note repo with agent context, disentangled transportable and personal part
3. Workflows
4. Ciritical thinking against hallucination
The first is what I can learn from, others I have found similar principle on my own.

# Claude Code

CLI first, the assumption is agent spending a long time to build and test, user use `/btw` to ask side questions without interrupting it.
A good practice might be use Cursor for coding (focused on writing), Claude Code for env/build/test/fix/deploy.. (focused on tool call)
`ctrl+o` to expand or collapse tool call details.

## Planning
shift+tab to cycle modes, default -> auto-accept-edit -> plan. Can also invoke plan mode verbally or via /plan.
Auto-accept edit just allows file edit, other tool calls still need to be confrimed.
Auto-TODO list is builtin, ask for it if it does not appear.

## Session Management
Type exit to exit, /context /compact and /clear for context management.

## Prompting
1. User level `~/.claude/CLAUDE.md`,
2. CLAUDE.md at project root.
3. Path scoped `.claude/rules/`, similar to Cursor

## Allowlist and Automation
Notice that it uses CLI, does not assume user interaction like Cursor, natural fit for running in a tmux without user interaction? No, user approval is needed for tool call, full automation is possible but not recommended.
Edit ~/.claude/settings.json (global) or .claude/settings.json (per-project, commit this) to configurate allow list. Not sure the balance that keeps it automated enough while keeping the risk acceptable -- in theory I should have a conservative allow list and read ever other tool call before allowing it. The safety protocol will be useless if I just keep hitting enter for yes without reading.

## RAG
Claude manages a Auto Memory.
