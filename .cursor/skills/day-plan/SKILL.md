---
name: day-plan
description: Help Henry drafting his day plan as `todo.mdc` in the morning.
---

# Day Planning

Start the day by discussing Henry's plan. Schedule open tasks into available time slots using the [Task DSL](../../rules/plan.mdc#task-dsl). Send an intuitive list of due and available tasks.

1. Run `py .cursor/skills/day-plan/scripts/task_manager/list_task.py` to see unscheduled and upcoming tasks.
2. Flag unscheduled tasks — every task needs a date. Ask Henry to find a date for it.
3. Reschedule overdue tasks for today, without changing the due date.
4. Update `.cursor/rules/todo.mdc` with today's plan, grouped by time slots (morning, afternoon, evening). Omit list ordinals, since Henry will reorder to confirm his priorities.
5. Append source links using markdown section anchors (e.g. `[2026-05-19.md > Afternoon](/log/2026-05-19.md#afternoon)`). Do not use line numbers — they break when the file is edited.
6. List tasks with an exact time and ask Henry to set alarms.
