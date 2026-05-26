---
name: critic
description: Review and distill knowledge from updates. Offloaded to a separate agent.

---

For an agent, writing is in-context learning.
Postmortem hindsight analysis (critic) is separated from execution (actor and user) to avoid distraction and context bloat; a separate agent — not the original executor — reviews the learned experience to ensure it is reusable.
The actor runs tasks and dumps raw experience to `log/`; Henry writes to the log and knowledge directly; the critic (this skill) distills both into the knowledge base.

# Check the Updates
If specific content is mentioned, critique only that; otherwise critique the whole update.
First `.agent/skills/critic/scripts/critic.sh pull` to rebase the current branch (with autostash) onto remote and fast-forward the `learner-baseline` (marker of the commit of the last scan).
Run `.agent/skills/critic/scripts/critic.sh diff --name-only` to list files changed since the last scan, or `critic.sh diff` for the full diff.
Uncommitted work is excluded by default; add `--include-wip` to preview it.
For each diff, read the surrounding text and referenced links to understand the context, then apply the steps below to integrate the new experience into the knowledge base.

# [Review](actor#fact-finding)
Check the update for consistency and completeness of the claims.
If the log is about implementing code, review the code as well.
Flag conflicts and remove inaccurate or outdated information.
Logs are immutable; amendments should be appended, not modified in place.
If a claim lacks support: when it is Henry's, leave the text and flag inline `[^unsupported_label]`; when it is yours, rewrite to match what you actually found.

## Long Term Planning
Challenge the necessity and effectiveness of the plans and decisions.

Whenever you identify a goal or task, draft a plan of actionable subtasks in priority order so Henry is prepared. Example: for Henry's US internship `log/2026-05-07.md`, the top priority subtasks are:
1. Immigration — visa type and timing, supporting documents.
2. Relocation — flight and housing, with dates aligned (visa start → flight → housing → intern start).
3. Finances — US banking or transfer route for payroll, currency conversion ahead of expenses, emergency cash.
4. Communications — US SIM live before landing.

This also applies to long-term goals, so open a task for Henry to discuss his research plan during internship.

When you see a task, make sure it has sensible timestamps and is properly scheduled. Every task must have a scheduled or due date so it can be reviewed or rescheduled.

# Normalize
New experiences are dumped to `log/` by the actors; entries are append-only and immutable (event sourcing).
Single source of truth: each fact has one authoritative location, referenced everywhere else.
The log is the source of truth for events — what happened, when, in what context, including dead ends. The knowledge base is the source of truth for knowledge — durable lessons stripped of contingent context, derived from events.
Duplicate records should be replaced by reference to the source of truth.
Once events accumulate, distill from the log into the knowledge base: put factual knowledge in `knowledge/` (per topic), `reading/` (per source), or `work/` (per project); put behavior learning in `rules/` or `skills/`.
For large projects, the source of truth may be delegated to its own repo instead of `work/`; the normalize step should then update the repo's documentation from the `note/log/` entries.
Keep insignificant or one-off lessons in the day's log.

# Fix
Fix typos, grammar, and clumsy expressions without changing meaning.
Make it sound natural to native speakers.
Add or fix references `[label](path_or_url#section)`, list numbering, and heading consistency.
Relative path is relative to the file being edited, absolute path relative to repo root.
Avoid ordinals in headings — they complicate reorganization and break references when moved.
Avoid markdown bold and italic — wastes tokens.
Translation other languages to English, except for quotes and identifiers.

# Optimize
First fix.
Verbosity harms readability, wastes attention and tokens.
Write as concisely as the rule files. Focus on what and why, not how.
Use the shortest expression without losing information; elaborate only when asked.
Make structural changes: reorder sentences and paragraphs to bring related topics closer and make the article flow logically; merge duplicates.
Split a note when a self-contained section can be reused independently.
Keep `rules/` and `skills/` concise: only add new rules or patterns — repeating a failed rule does not help.
Keep notes `grep`-friendly: use predictable, consistent terms, keywords, and identifiers so you can retrieve them easily later.

# Commit and Sync
After consolidating, run `.agent/skills/critic/scripts/critic.sh commit -a -m "<message>"` once the user approves your edits; `commit` itself runs as `Galatea` so the repo's default identity stays Henry's. If Henry has in-progress edits in the working tree that should not be in the critic commit, ask before committing — `-a` would otherwise absorb them.
Run `.agent/skills/critic/scripts/critic.sh sync` to pull, mark HEAD as the new `learner-baseline`, push the current branch and the marker, and possess Devmate + Claude at `$HOME` and Cursor at the note repo. If the pull brings remote updates, `sync` stops so you can review them first; re-run `sync` once reviewed.
Remind Henry to learn from significant new lessons; that's part of sync.
