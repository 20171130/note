"""
Returns all tasks in the workspace notes.
A task is a line in a markdown file starting with - [ ] or - [/] (inprogress) or - [x] or - [X] (done) followed by a space and the task body.
Ignores .cursor and .git directories.
Returns tasks with their source file and line number.
By default only returns unfinished tasks, use --all to return all tasks..

If a relative recurring task is found together with a finished instance, automatically increment dates:
- 🔁 recurring
    relative, e.g. `🔁 every 3 days`, increments based on actual finished date
    aboslute, e.g. `🔁 every weekday`, `🔁 every week on Monday`, used without scheduled date, no need to touch

Example:
- [ ] Task 1 🔁 every 3 days ⏳ 2026-05-14
- [x] Task 1 ✅ 2026-05-16
Next: ⏳ 2026-05-19
No need to touch start and due date if they exist.
"""

import datetime
import os
import re
from dataclasses import dataclass
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[5]

EXCLUDE_DIRS = {".obsidian", ".git", ".cursor"}

TASK_RE = re.compile(r"^\s*- \[([ /xX])\] (.*)$")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")

SCHED_EMOJI = "⏳"
DUE_EMOJI = "📅"
RECUR_EMOJI = "🔁"

DOW = {
    "sunday": 0,
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
}


@dataclass
class Task:
    body: str
    state: str  # " " (todo) or "/" (in progress)
    source: Path  # relative to WORKSPACE_ROOT
    line: int  # line number in the source file
    scheduled: str | None  # YYYY-MM-DD from ⏳
    due: str | None  # YYYY-MM-DD from 📅
    cron_expr: str | None  # 5-field cron expression if 🔁 was translatable
    section: str | None = None  # nearest heading above the task


def field_matches(field: str, value: int) -> bool:
    if field == "*":
        return True
    for part in field.split(","):
        if "/" in part:
            base, step = part.split("/")
            start = 0 if base == "*" else int(base)
            if value >= start and (value - start) % int(step) == 0:
                return True
        elif "-" in part:
            lo, hi = map(int, part.split("-"))
            if lo <= value <= hi:
                return True
        elif int(part) == value:
            return True
    return False


def cron_matches(expr: str, today: datetime.date) -> bool:
    if expr.startswith("every "):
        m = re.match(r"every (\d+) days from (\d{4}-\d{2}-\d{2})", expr)
        if m:
            interval = int(m.group(1))
            start_date = datetime.date.fromisoformat(m.group(2))
            if today >= start_date:
                return (today - start_date).days % interval == 0
        return False

    _min, _hour, dom, mon, dow = expr.split()
    # cron DOW: Sun=0..Sat=6. Python isoweekday: Mon=1..Sun=7.
    cron_dow = today.isoweekday() % 7
    return (
        field_matches(dom, today.day)
        and field_matches(mon, today.month)
        and field_matches(dow, cron_dow)
    )


def extract_date_after(text: str, emoji: str) -> str | None:
    idx = text.find(emoji)
    if idx == -1:
        return None
    m = DATE_RE.search(text, idx)
    return m.group(1) if m else None


def parse_recurrence(body: str, scheduled: str | None) -> str | None:
    idx = body.find(RECUR_EMOJI)
    if idx == -1:
        return None
    tail = body[idx + len(RECUR_EMOJI) :].lower().strip()
    if re.match(r"every day\b", tail):
        return "0 3 * * *"
    if re.match(r"every weekday\b", tail):
        return "0 3 * * 1-5"
    m = re.match(r"every week(?: on)? ([a-z,]+)", tail)
    if m:
        days = [DOW[d.strip()] for d in m.group(1).split(",") if d.strip() in DOW]
        if days:
            return f"0 3 * * {','.join(map(str, days))}"
    if re.match(r"every week\b", tail) and scheduled:
        cron_dow = datetime.date.fromisoformat(scheduled).isoweekday() % 7
        return f"0 3 * * {cron_dow}"
    m = re.match(r"every month(?: on the )?(\d+)(?:st|nd|rd|th)?", tail)
    if m:
        return f"0 3 {int(m.group(1))} * *"
    if re.match(r"every month\b", tail) and scheduled:
        return f"0 3 {datetime.date.fromisoformat(scheduled).day} * *"
    m = re.match(r"every (\d+) days\b", tail)
    if m and scheduled:
        return f"every {m.group(1)} days from {scheduled}"
    return None


def get_base_body(body: str) -> str:
    idx = len(body)
    for emoji in ["⏳", "📅", "🔁", "✅", "➕", "🛫"]:
        i = body.find(emoji)
        if i != -1 and i < idx:
            idx = i
    return body[:idx].strip()


def cron_period_days(cron_expr: str) -> int | None:
    """Return the fixed day interval for simple patterns, or None for complex ones."""
    m = re.match(r"every (\d+) days from", cron_expr)
    if m:
        return int(m.group(1))
    if cron_expr == "0 3 * * *":
        return 1
    if re.match(r"0 3 \* \* [\d,]+$", cron_expr):
        return 7
    return None


def _next_cron_after(cron_expr: str, from_date: datetime.date) -> datetime.date:
    d = from_date + datetime.timedelta(days=1)
    for _ in range(365 * 5):
        if cron_matches(cron_expr, d):
            return d
        d += datetime.timedelta(days=1)
    return d


def get_finished_date(task: Task) -> datetime.date | None:
    if task.state not in ("x", "X"):
        return None

    idx = task.body.find("✅")
    if idx != -1:
        m = DATE_RE.search(task.body, idx)
        if m:
            return datetime.date.fromisoformat(m.group(1))

    m = DATE_RE.search(task.source.name)
    if m:
        return datetime.date.fromisoformat(m.group(1))

    return None


def find_note_files(root: Path = WORKSPACE_ROOT) -> list[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if filename.endswith(".md"):
                files.append(Path(dirpath) / filename)
    return files


def parse_all_tasks(
    root: Path = WORKSPACE_ROOT, include_all: bool = False
) -> list[Task]:
    tasks: list[Task] = []
    for filepath in find_note_files(root):
        source_rel = filepath.relative_to(root)
        with open(filepath, encoding="utf-8") as f:
            in_code_block = False
            current_section = None
            for line_idx, raw in enumerate(f, start=1):
                if raw.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    continue

                hm = HEADING_RE.match(raw.rstrip())
                if hm:
                    current_section = hm.group(2).strip()
                    continue

                m = TASK_RE.match(raw)
                if not m:
                    continue
                state, body = m.group(1), m.group(2).strip()
                if state not in (" ", "/", "x", "X") or not body:
                    continue
                scheduled = extract_date_after(body, SCHED_EMOJI)
                due = extract_date_after(body, DUE_EMOJI)
                cron_expr = parse_recurrence(body, scheduled or due)
                tasks.append(
                    Task(
                        body=body,
                        state=state,
                        source=source_rel,
                        line=line_idx,
                        scheduled=scheduled,
                        due=due,
                        cron_expr=cron_expr,
                        section=current_section,
                    )
                )

    # Post-processing: find latest finished date for each base body
    latest_finished: dict[str, datetime.date] = {}
    for t in tasks:
        if t.state in ("x", "X"):
            base = get_base_body(t.body)
            fdate = get_finished_date(t)
            if fdate:
                if base not in latest_finished or fdate > latest_finished[base]:
                    latest_finished[base] = fdate

    # Update recurring tasks — only relative (interval-based) recurrence needs date increments.
    # Absolute recurrence (every weekday, every week on Monday, etc.) fires by cron, nothing to touch.
    for t in tasks:
        if t.state not in ("x", "X") and t.cron_expr:
            if not t.cron_expr.startswith("every "):
                continue  # absolute — no dates to advance
            base = get_base_body(t.body)
            if base not in latest_finished:
                continue
            fdate = latest_finished[base]
            period = cron_period_days(t.cron_expr)
            # Only advance ⏳ (scheduled) from the finished date; never touch 📅 (due).
            next_sched = (
                fdate + datetime.timedelta(days=period)
                if period
                else _next_cron_after(t.cron_expr, fdate)
            )
            if t.scheduled:
                sched_date = datetime.date.fromisoformat(t.scheduled)
                if next_sched > sched_date:
                    t.scheduled = next_sched.isoformat()
                    t.cron_expr = parse_recurrence(t.body, t.scheduled)
            else:
                t.scheduled = next_sched.isoformat()
                t.cron_expr = parse_recurrence(t.body, t.scheduled)

    if not include_all:
        tasks = [t for t in tasks if t.state not in ("x", "X")]

    return tasks


if __name__ == "__main__":
    import argparse
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--all", action="store_true", help="Return all tasks")
    args = ap.parse_args()
    for t in parse_all_tasks(include_all=args.all):
        print(f"{t.source}:{t.line} [{t.state}] {t.body}")
