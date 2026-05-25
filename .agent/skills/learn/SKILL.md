---
name: learn
description: Distill recent repo changes into knowledge, rules, and skills. Invoke for postmortem hindsight analysis after the user makes commits.
---

For an agent, writing is in-context learning.
Postmortem hindsight analysis is separated from execution to avoid distraction and context bloat; a separate agent — not the original executor — reviews the learned experience to ensure it is reusable.

# Workflow
Run `.agent/skills/learn/scripts/learn.sh --files` to list files changed since the last scan, or without `--files` for the full diff.
Uncommitted work is excluded by default; add `--include-wip` to preview it.
For each diff, read the surrounding text and referenced links to understand the context, then apply the steps below to integrate the new experience into the knowledge base.

After consolidating, commit once the user approves your edits, then run `.agent/skills/learn/scripts/learn.sh --mark` to record the new baseline. The baseline is stored as the git branch `learner-baseline` so it syncs via push/pull.

# Fix
First review (Fact Finding), flag conflicts and remove duplicates, inaccurate or outdated information.
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
Make structural changes: reorder and merge sentences and paragraphs to bring related topics closer and make the article flow logically.

# Learning and Normalize
Single source of truth: each fact has one authoritative location, referenced everywhere else.
Dump new experiences to `log/` first. Once they accumulate, distill: keep insignificant lessons in the day's log; move factual knowledge to `knowledge/` (per topic), `reading/` (per source), or `work/` (per project); move behavior learning to `rules/` or `skills/`.
After consolidating, replace originals with references.
Split a note when a self-contained section can be reused independently.
Keep `rules/` and `skills/` concise: only add new rules or patterns — repeating a failed rule does not help.
Keep notes `grep`-friendly: use predictable, consistent terms, keywords, and identifiers so you can retrieve them easily later.
Remind Henry to learn from the new lessons as well.

# Long Term Planning
Whenever you identify a goal or task, draft a plan of actionable subtasks in priority order so Henry is prepared. Example: for Henry's US internship `log/2026-05-07.md`, the top priority subtasks are:
1. Immigration — visa type and timing, supporting documents.
2. Relocation — flight and housing, with dates aligned (visa start → flight → housing → intern start).
3. Finances — US banking or transfer route for payroll, currency conversion ahead of expenses, emergency cash.
4. Communications — US SIM live before landing.

This also applies to long-term goals, so open a task for Henry to discuss his research plan during internship.

When you see a task, make sure it has sensible timestamps and is properly scheduled. Every task must have a scheduled or due date so it can be reviewed or rescheduled — a vague wishlist item is better off deleted than left to be procrastinated indefinitely.
