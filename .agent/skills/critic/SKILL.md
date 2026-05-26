---
name: learn
description: Distill recent experience into knowledge, rules, and skills. Offloaded to a separate agent.
---

For an agent, writing is in-context learning.
Postmortem hindsight analysis (critic) is separated from execution (actor and user) to avoid distraction and context bloat; a separate agent — not the original executor — reviews the learned experience to ensure it is reusable.
The actor runs tasks and dumps raw experience to `log/`; Henry writes log and knowledge directly; the critic (this skill) distills both into the knowledge base.

# Check the Updates
First `.agent/skills/learn/scripts/learn.sh pull` to fast-forward both the current branch and the `learner-baseline` (marker of the commit of the last scan) from the remote.
Run `.agent/skills/learn/scripts/learn.sh diff --name-only` to list files changed since the last scan, or `learn.sh diff` for the full diff.
Uncommitted work is excluded by default; add `--include-wip` to preview it.
For each diff, read the surrounding text and referenced links to understand the context, then apply the steps below to integrate the new experience into the knowledge base.

# Normalize
New experiences are dumped to `log/` by the actors; entries are append-only and immutable.
Single source of truth: each fact has one authoritative location, referenced everywhere else.
The log is the source of truth for events — what happened, when, in what context, including dead ends. The knowledge base is the source of truth for knowledge — durable lessons stripped of contingent context, derived from events.
Duplicate records should be replaced by reference to the source of truth.
Once events accumulate, distill from the log into the knowledge base: put factual knowledge in `knowledge/` (per topic), `reading/` (per source), or `work/` (per project); put behavior learning in `rules/` or `skills/`. Keep insignificant or one-off lessons in the day's log.

# Fix
First review (Fact Finding); flag conflicts and remove inaccurate or outdated information.
Fix typos, grammar, and clumsy expressions without changing meaning.
Make it sound natural to native speakers.
Add or fix references `[label](path_or_url#section)`, list numbering, and heading consistency.
Relative path is relative to the file being edited, absolute path relative to repo root.
Avoid ordinals in headings — they complicate reorganization and break references when moved.
Avoid markdown bold and italic — wastes tokens.

# Optimize
First fix.
Verbosity harms readability, wastes attention and tokens.
Write as concisely as the rule files. Focus on what and why, not how.
Use the shortest expression without losing information; elaborate only when asked.
Make structural changes: reorder sentences and paragraphs to bring related topics closer and make the article flow logically; merge duplicates.
Split a note when a self-contained section can be reused independently.
Keep `rules/` and `skills/` concise: only add new rules or patterns — repeating a failed rule does not help.
Keep notes `grep`-friendly: use predictable, consistent terms, keywords, and identifiers so you can retrieve them easily later.

# Long Term Planning
Whenever you identify a goal or task, draft a plan of actionable subtasks in priority order so Henry is prepared. Example: for Henry's US internship `log/2026-05-07.md`, the top priority subtasks are:
1. Immigration — visa type and timing, supporting documents.
2. Relocation — flight and housing, with dates aligned (visa start → flight → housing → intern start).
3. Finances — US banking or transfer route for payroll, currency conversion ahead of expenses, emergency cash.
4. Communications — US SIM live before landing.

This also applies to long-term goals, so open a task for Henry to discuss his research plan during internship.

When you see a task, make sure it has sensible timestamps and is properly scheduled. Every task must have a scheduled or due date so it can be reviewed or rescheduled — a vague wishlist item is better off deleted than left to be procrastinated indefinitely.

# Commit and Sync
After consolidating, run `.agent/skills/learn/scripts/learn.sh commit -m "<message>"` once the user approves your edits — this commits as `Galatea` so the repo's default identity stays Henry's.
Run `.agent/skills/learn/scripts/learn.sh sync` to pull, mark HEAD as the new `learner-baseline`, push the current branch and the marker, and possess Devmate + Claude at `$HOME` and Cursor at the note repo. If the pull brings remote updates, `sync` stops so you can review them first; re-run `sync` once reviewed.
Remind Henry to learn from the new lessons as well, that's a part of sync.
