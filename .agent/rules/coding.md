---
description: Code style and debugging: minimize code, no error handling unless asked, let it crash, root-cause first.
globs: **/*.py, **/*.ts, **/*.tsx, **/*.js, **/*.jsx, **/*.go, **/*.rs, **/*.c, **/*.cc, **/*.cpp, **/*.h, **/*.hpp, **/*.java, **/*.sh, **/*.ps1, **/*.rb, **/*.lua, **/*.zig, **/*.swift, **/*.kt, **/*.scala
alwaysApply: false
---

# Code Style

1. MINIMIZE CODE
   Write only what is explicitly requested. Do not add anything extra.

2. LET IT CRASH
   Do not add error handling unless failure is inherently non-deterministic (e.g. network I/O).
   → No try/except blocks, guards, or fallback branches.
   → Stack traces are valuable; error handling hides bugs.
   → Do not add checks like `if x is not None` when `x` is expected to exist.

3. NO UNEXPECTED DEFAULT VALUES
   → Do not use safe accessors like `dict.get(key, default)` or `getattr(obj, attr, default)`.
   → Default values are allowed only in function signatures and `argparse`.
   → If a required key or attribute is missing, let the program crash.

4. TIME EXPECTATION
   Before running any time-consuming job, tell the user the expected duration so an unexpected timeout is recognizable. Do not block on the call — launch in background and stream unbuffered output to a text file.

# Debugging

1. Always identify the root cause before attempting any fix.
2. If the cause is obvious, explain it clearly to the user.
3. If the cause is not obvious, propose plausible hypotheses and discuss them with the user.
4. Only after the user approves a hypothesis, add targeted debug logging or instrumentation to test it.

# Lessons Learned
- Ask before treating a committed credential as leaked. If the repo is private, save the key locally and make rotation optional.
- Ask whether backward compatibility is needed on major changes. If Henry explicitly allows a new branch and no legacy compatibility, delete obsolete paths instead of deprecating them.
- When choosing a runtime on an unfamiliar cluster, first probe an interactive compute job. See [VPO debugging lesson](/work/VPO.md#debugging-lesson).
- To wait for a backgrounded child process, use `wait $PID` or `kill -0 $PID`, not `pgrep -af '<pattern>'`. The shell running the poll loop has the pattern in its own argv, so pgrep matches itself and never returns false → infinite hang.
- For long-running jobs (sbatch, multi-GB transfers, container pulls), do not block one tool call polling them. Submit, return to Henry, check status next turn. Multi-minute silent waits burn his time and prevent course-correction.
- Before building a workaround for a missing asset (image, dataset, checkpoint), enumerate where copies might exist across all reachable systems Henry uses — other clusters, /checkpoint/* mounts, shared team paths. Ask if you can't enumerate. A 5-min scp from another cluster usually beats hours of recreating.
- When comparing an aggregated metric (MAE, accuracy) against a published number, print one raw `(pred, true)` pair first to confirm unit and convention. A 100× discrepancy is almost always a units bug, not a model bug, and is caught in a 5-min `--limit 3 --verbose` run.
- Before forking a multi-GB container image to add a dependency, check ABI/version pins (`curl pypi.org/pypi/<pkg>/json`). A 30 s curl beats a 16 min rebuild + likely uninstall/reinstall cycle.
- When pattern-matching on an exception message in Python, walk `traceback.format_exception(e)`, not just `str(e)`. Chained `__cause__` text isn't in `str(e)` and breaks naive `if "foo" in str(e):` predicates.
- Don't trust "X uses Y, so Y works" inheritance. Run Y end-to-end yourself once before planning around it — cluster docs and inherited recipes go stale silently.
