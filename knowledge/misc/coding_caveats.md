Operational caveats from past debugging — narrow lessons, not always-loaded rules. Each is a one-line trap with the cheap check that beats the expensive recovery.

# Credentials and Compatibility
- A committed credential in a private repo is not necessarily leaked; ask before rotating. Save the key locally and make rotation optional.
- Ask whether backward compatibility is needed on major changes. If Henry allows a new branch with no legacy support, delete obsolete paths instead of deprecating them.

# Cluster and Runtime
- On an unfamiliar cluster, probe runtime in an interactive compute job before scripting. See [VPO debugging lesson](../../work/VPO.md#debugging-lesson).
- Don't trust "X uses Y, so Y works" inheritance. Run Y end-to-end once before planning around it; cluster docs and inherited recipes go stale silently.
- Before forking a multi-GB container image to add a dependency, check ABI/version pins (`curl pypi.org/pypi/<pkg>/json`). A 30 s curl beats a 16 min rebuild plus likely uninstall cycle.
- Before building a workaround for a missing asset (image, dataset, checkpoint), enumerate copies across reachable systems — other clusters, `/checkpoint/*`, shared team paths. A 5-minute scp usually beats hours of recreating.

# Process Management
- To wait for a backgrounded child, use `wait $PID` or `kill -0 $PID`, not `pgrep -af '<pattern>'`. The polling shell has the pattern in its own argv, so pgrep matches itself and never returns false → infinite hang.
- For long-running jobs (sbatch, multi-GB transfers, container pulls), don't block one tool call polling them. Submit, return to Henry, check status next turn. Multi-minute silent waits burn his time and prevent course-correction.

# Numerics and Errors
- When comparing an aggregated metric (MAE, accuracy) against a published number, print one raw `(pred, true)` pair first to confirm unit and convention. A 100× discrepancy is almost always a units bug, caught by a 5-min `--limit 3 --verbose` run.
- When pattern-matching on a Python exception, walk `traceback.format_exception(e)`, not just `str(e)`. Chained `__cause__` text isn't in `str(e)` and breaks naive `if "foo" in str(e):` predicates.

# Capacity and Saturation Tests
- A saturation claim must come from a held-out generalization test, not single-record memorization. 100% bit-exact on one sample only proves the test fits in capacity; it says nothing about whether the architecture is invertible on the distribution. See [log 2026-05-26 01:06](../../log/2026-05-26.md#2026-05-26-0106-pdt--codec-is-the-real-bottleneck-h-broadcast-fixes-it-capacity-floor-d_inner128).
- Identifying a capacity floor: treat any non-100% on eval as fail. 99.9% at N steps is "close at this schedule", not the floor; the floor is the smallest config that hits the exact target.
- When a failure mode has a specific information-flow story (e.g. conditioning has to travel K−1 causal hops), try the targeted fix (broadcast/inject the missing signal at every position) before scaling capacity. Architectural fixes can swing a metric from 19% → 100% at constant width.
