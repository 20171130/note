
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

# Principles
Dex Horthy observed a sweet zone: LLM is the best within the first 100K tokens.
This induces the first two principles.

## Memory hierarchy
 just like my global rules - optional rules - knowledge - log
file system instead of vector database
frequent intentional compaction, or init from file system
Some find json is better than markdown since AI is less likely to fuck up structured data without syntax error.
上下文窗口污染缓解：最小化控制台输出，日志写入文件，使用 grep 友好的错误格式（ERROR: [reason] 单行），预计算聚合统计而非输出原始数据。

## Agent collaboration
Needed only when single agent context becomes longer than sweet zone.
Or when there are different priorities, like plan-execution-logging vs learning and consolidation.
Single agent where we can, multiagent where we must.

## Workflow
Plan and verification, this is what I should incorporate
consolidation should be a background task, from the perspective of a agent without context mimicing an agent reading this after fresh start

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

## Prompt
Cursor adds prompts like this, partially explaining Galatea felt more inorganic on Cursor then OpenClaw.
These live in your Cursor user rules and apply every turn:

Git commits — Only commit when you ask; safety protocol (no config changes, no destructive git, no --no-verify, amend rules, parallel status/diff/log, HEREDOC commit messages, no push unless asked).

Pull requests — Use gh for GitHub; parallel prep commands; structured PR body; return PR URL; no TodoWrite/Task for PR flow.

Follow all instructions — User rules, tool rules, system reminders, skills, MCP instructions must be followed completely.

Real environment — Full shell/network access; I must run commands and retry, not give up after one failure.

Communication — Code citations as startLine:endLine:filepath; citation fences on their own line; full URLs/paths; blog-quality prose; proportional responses; sparing bold/backticks; no engagement bait.

Conversation intent — Infer goal from history; mid-task messages are usually steering, not canceling.

Coding principles — Minimize scope; no over-engineering; match existing conventions; comments only when non-obvious; tests only when requested or meaningful.




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
No ned to use Plan mode, just ask it to write a plan. Agents are so flexible that the best practice of using it is a large part of the product.

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

# Practice

A good practice is to keep a personal knowledge base with rules copied to ~/ shared by all projects.
Use a single source of rules, derive cursor or claude variants.
Meta DevMate has yet another format.

Devmate docs specify
*.md
.
Cursor project rules convention is .cursor/rules/*.mdc.
Cursor’s alwaysApply: true is Cursor-specific.
Devmate’s rule filters use fields like apply_to_path, apply_to_user_prompt, include_rule, etc.
Devmate docs do not mention *.mdc.
Cursor generally expects .mdc files in .cursor/rules; I would not assume it loads .md there.
