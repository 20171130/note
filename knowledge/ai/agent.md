
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
1. User level `~/.claude/CLAUDE.md`, 
2. CLAUDE.md at project root.
3. Path scoped `.claude/rules/`, similar to Cursor

## RAG
Claude manages a Auto Memory.

