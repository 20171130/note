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

5. LOGGING AND MLOPS — JSONL ALONGSIDE THE DASHBOARD
   When training runs / long jobs log to a human dashboard (wandb, tensorboard, mlflow…), also write the same scalars as JSONL files under `project_root/logs/`. Dashboards are web-only and require auth — opaque to the LLM; the JSONL files are `tail`/`grep`/`jq`-able and give the agent identical observability.

# Debugging

1. Always identify the root cause before attempting any fix.
2. If the cause is obvious, explain it clearly to the user.
3. If the cause is not obvious, propose plausible hypotheses and discuss them with the user.
4. Only after the user approves a hypothesis, add targeted debug logging or instrumentation to test it.

See [coding caveats](/knowledge/misc/coding_caveats.md) for narrow operational traps from past debugging — load on demand, not always.
