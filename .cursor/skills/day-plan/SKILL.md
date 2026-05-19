---
name: day-plan
description: Help Henry drafting his day plan as `todo.mdc` in the morning.
---

# Day Planning

Start the day by discussing Henry's plan. Schedule open tasks into available time slots. Send an intuitive list of due and available tasks. Confirm the plan before writing it down.

1. Run `py .cursor/skills/day-plan/scripts/task_manager/list_task.py` to see unscheduled and upcoming tasks.
2. Flag unscheduled tasks — every task need a date.
3. Reschedule overdue tasks for today.
4. Update `.cursor/rules/todo.mdc` with today's plan, grouped by time slots (morning, afternoon, evening). Omit list ordinals, since Henry will reorder to confirm his priorities.
5. Append absolute source links relative to repo root (e.g. `/log/{date}.md#L12` ).


## Task DSL

- ⏳ scheduled — when to prepare/act
- 📅 due — actual date the event/deadline occurs (⏳ wins if both present)
- 🔁 recurring — e.g. `🔁 every weekday`, `🔁 every week on Monday`, `🔁 every 3 days`
- `[ ]` todo, `[/]` in progress, `[x]` done with `✅ YYYY-MM-DD`