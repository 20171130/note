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
import re
import sys
from pathlib import Path

from task_parse import cron_matches, get_base_body, parse_all_tasks

sys.stdout.reconfigure(encoding="utf-8")

WINDOW_DAYS = 7
TIME_PREFIX_RE = re.compile(r"^(?:\d{1,2}:\d{2}(?:\s*-\s*\d{1,2}:\d{2})?\s+)")
RECUR_TEXT_RE = re.compile(r"🔁[^⏳📅✅➕🛫]*")


def task_key(task) -> tuple[str, str | None]:
    base = TIME_PREFIX_RE.sub("", get_base_body(task.body)).strip().lower()
    m = RECUR_TEXT_RE.search(task.body)
    recur = m.group(0).strip() if m else None
    return base, recur


def source_date(task) -> datetime.date | None:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", task.source.name)
    return datetime.date.fromisoformat(m.group(1)) if m else None


def prefer_task(a, b):
    """Pick the canonical copy when the same task appears in multiple notes."""
    a_recurring = (a.section or "").lower() == "recurring"
    b_recurring = (b.section or "").lower() == "recurring"
    if a_recurring != b_recurring:
        return a if a_recurring else b

    a_date = source_date(a)
    b_date = source_date(b)
    if a_date and b_date and a_date != b_date:
        return a if a_date > b_date else b
    if a_date and not b_date:
        return a
    if b_date and not a_date:
        return b

    if a.source != b.source:
        return a if str(a.source) > str(b.source) else b
    return a if a.line >= b.line else b


def dedupe_tasks(tasks):
    best: dict[tuple[str, str | None], object] = {}
    for t in tasks:
        key = task_key(t)
        if key not in best:
            best[key] = t
        else:
            best[key] = prefer_task(best[key], t)
    return list(best.values())


def is_interval_cron(cron_expr: str | None) -> bool:
    """Interval-based recurrence (e.g. 'every 3 days') — treated as unscheduled."""
    return cron_expr is not None and cron_expr.startswith("every ")


def heading_to_anchor(heading: str) -> str:
    """Convert a markdown heading to a GitHub/Obsidian-style anchor."""
    anchor = heading.lower().strip()
    anchor = re.sub(r"[^\w\s-]", "", anchor)
    anchor = re.sub(r"\s+", "-", anchor)
    return anchor


def format_link(task) -> str:
    rel_path = "/" + task.source.as_posix()
    if task.section:
        anchor = heading_to_anchor(task.section)
        return f"[{task.source.name} > {task.section}]({rel_path}#{anchor})"
    return f"[{task.source.name}]({rel_path})"


def earliest_fire(task, today: datetime.date, window_days: int) -> datetime.date | None:
    end = today + datetime.timedelta(days=window_days)
    candidates: list[datetime.date] = []

    ref_str = task.scheduled or task.due
    if ref_str:
        sched_date = datetime.date.fromisoformat(ref_str)
        if sched_date <= end:
            candidates.append(sched_date)

    if task.cron_expr and not is_interval_cron(task.cron_expr):
        for offset in range(window_days + 1):
            date = today + datetime.timedelta(days=offset)
            if cron_matches(task.cron_expr, date):
                candidates.append(date)
                break

    return min(candidates) if candidates else None


def collect_upcoming(tasks, today: datetime.date, window_days: int):
    rows = []
    for t in tasks:
        if t.cron_expr:
            if is_interval_cron(t.cron_expr):
                continue
            fire_date = earliest_fire(t, today, window_days)
            if fire_date is not None:
                rows.append((fire_date, t))
        elif ref_str := t.scheduled or t.due:
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
        print(
            f"  {fire_date} {date_tag(fire_date, today)} {marker_of(t)} {t.body}  {format_link(t)}"
        )
    print()


def print_recurring(tasks):
    rec = sorted(
        [t for t in tasks if t.cron_expr and not is_interval_cron(t.cron_expr)],
        key=lambda t: t.cron_expr,
    )
    print(f"# Recurring ({len(rec)})")
    for t in rec:
        print(f"  {marker_of(t)} {t.body}  {format_link(t)}  (cron: {t.cron_expr})")
    print()


def print_unscheduled(tasks):
    free = [
        t
        for t in tasks
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
    ap.add_argument(
        "--upcoming",
        type=int,
        nargs="?",
        const=0,
        default=0,
        help="show upcoming tasks (scheduled, due or overdue in the next N days)",
    )
    ap.add_argument(
        "--finished", action="store_true", help="show finished/completed tasks"
    )
    ap.add_argument("--all", action="store_true", help="show all tasks")
    args = ap.parse_args()

    today = datetime.date.today()

    # We want to filter out finished tasks from upcoming, unscheduled, and recurring,
    # unless we are building the finished bucket explicitly.
    all_tasks = dedupe_tasks(parse_all_tasks(include_all=True))

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
