#!/usr/bin/env python3
"""

Calls task_parse.py to list tasks in the workspace notes, and groups them by category.
options: 
--upcoming N: show upcoming tasks (scheduled, due or overdue in the next N days)
    default --upcoming 0, only show today's tasks, Notice that a task without schedule or due date needs to be scheduled and is always upcoming.
--finished: show finished/completed tasks
--all: show all tasks

Notice that 
`🔁 every 3 days` is an unscheduled task
But `🔁 every week on Wednesday, Thursday` is scheduled 
"""
import argparse
import datetime
import sys
from pathlib import Path

from task_parse import cron_matches, parse_all_tasks

sys.stdout.reconfigure(encoding="utf-8")

WINDOW_DAYS = 7


def is_interval_cron(cron_expr: str | None) -> bool:
    """Interval-based recurrence (e.g. 'every 3 days') — treated as unscheduled."""
    return cron_expr is not None and cron_expr.startswith("every ")


def format_link(task) -> str:
    rel_path = "/".join(task.source.parts)
    return f"[{task.source.name}:{task.line}]({rel_path}#L{task.line})"


def collect_upcoming(tasks, today: datetime.date, window_days: int):
    rows = []
    for t in tasks:
        ref_str = t.scheduled or t.due
        # If it's a recurring task, project it forward into the window
        if t.cron_expr:
            # Interval-based recurrence (every N days) is unscheduled — skip here
            if is_interval_cron(t.cron_expr):
                continue
            if ref_str:
                sched_date = datetime.date.fromisoformat(ref_str)
                if sched_date <= today + datetime.timedelta(days=window_days):
                    if (sched_date, t) not in rows:
                        rows.append((sched_date, t))

                # Only project future occurrences if we are not currently overdue
                if sched_date >= today:
                    for offset in range(window_days + 1):
                        date = today + datetime.timedelta(days=offset)
                        if date > sched_date and cron_matches(t.cron_expr, date):
                            if (date, t) not in rows:
                                rows.append((date, t))
            else:
                for offset in range(window_days + 1):
                    date = today + datetime.timedelta(days=offset)
                    if cron_matches(t.cron_expr, date):
                        if (date, t) not in rows:
                            rows.append((date, t))
        # If it's just a one-off scheduled/due task
        elif ref_str:
            sched_date = datetime.date.fromisoformat(ref_str)
            if sched_date <= today + datetime.timedelta(days=window_days):
                rows.append((sched_date, t))
    rows.sort(key=lambda r: r[0])
    return rows


def date_tag(date: datetime.date, today: datetime.date) -> str:
    if date < today:
        return "[OVERDUE]"
    if date == today:
        return "[TODAY]  "
    return "         "


def marker_of(task) -> str:
    if task.state in ("x", "X"):
        return "[x]"
    return "[/]" if task.state == "/" else "[ ]"


def print_upcoming(rows, today):
    print(f"# Upcoming ({len(rows)})")
    for fire_date, t in rows:
        print(f"  {fire_date} {date_tag(fire_date, today)} {marker_of(t)} {t.body}  {format_link(t)}")
    print()


def print_recurring(tasks):
    rec = sorted([t for t in tasks if t.cron_expr and not is_interval_cron(t.cron_expr)], key=lambda t: t.cron_expr)
    print(f"# Recurring ({len(rec)})")
    for t in rec:
        print(f"  {marker_of(t)} {t.body}  {format_link(t)}  (cron: {t.cron_expr})")
    print()


def print_unscheduled(tasks):
    free = [
        t for t in tasks
        if t.state not in ("x", "X")
        and ((not t.cron_expr and not t.scheduled) or is_interval_cron(t.cron_expr))
    ]
    print(f"# UNSCHEDULED: Needs Scheduling & Attention ({len(free)})")
    for t in free:
        print(f"  {marker_of(t)} {t.body}  {format_link(t)}")
    print()


def print_finished(tasks):
    finished = [t for t in tasks if t.state in ("x", "X")]
    print(f"# Finished ({len(finished)})")
    for t in finished:
        print(f"  {marker_of(t)} {t.body}  {format_link(t)}")
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    ap.add_argument("--upcoming", type=int, nargs="?", const=0, default=0,
                    help="show upcoming tasks (scheduled, due or overdue in the next N days)")
    ap.add_argument("--finished", action="store_true", help="show finished/completed tasks")
    ap.add_argument("--all", action="store_true", help="show all tasks")
    args = ap.parse_args()

    today = datetime.date.today()
    
    # We want to filter out finished tasks from upcoming, unscheduled, and recurring,
    # unless we are building the finished bucket explicitly.
    all_tasks = parse_all_tasks(include_all=True)
    
    seen = set()
    deduped_tasks = []
    for t in all_tasks:
        if t.body not in seen:
            seen.add(t.body)
            deduped_tasks.append(t)
    all_tasks = deduped_tasks

    active_tasks = [t for t in all_tasks if t.state not in ("x", "X")]

    if args.all:
        print_unscheduled(active_tasks)
        print_upcoming(collect_upcoming(active_tasks, today, 7), today)
        print_recurring(active_tasks)
        print_finished(all_tasks)
        return 0

    if args.finished:
        print_finished(all_tasks)
        return 0

    # Default behavior or --upcoming
    print_unscheduled(active_tasks)
    print_upcoming(collect_upcoming(active_tasks, today, args.upcoming), today)

    return 0


if __name__ == "__main__":
    sys.exit(main())
