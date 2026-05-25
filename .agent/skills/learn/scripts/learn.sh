#!/usr/bin/env bash
# Show what changed in the note repo since the learner last scanned it.
#
# Baseline is stored in the git branch `learner-baseline` so it syncs via
# push/pull. If unset, falls back to the root commit (everything is new).
#
# Usage:
#   learn.sh                 print diff since the last scan (committed only)
#   learn.sh --files         print only the changed file paths
#   learn.sh --include-wip   also include uncommitted changes
#   learn.sh --mark          record HEAD as scanned (run after review)
#   learn.sh --base          print the current baseline commit
#   learn.sh -h | --help     show this help

set -euo pipefail

REF="refs/heads/learner-baseline"
cd "$(git rev-parse --show-toplevel)"

show_help() { sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; }

files_only=0
include_wip=0
for arg in "$@"; do
  case "$arg" in
    --mark)
      git update-ref "$REF" "$(git rev-parse HEAD)"
      echo "marked $(git rev-parse --short HEAD) as scanned (branch learner-baseline)" >&2
      echo "push with: git push origin learner-baseline" >&2
      exit 0 ;;
    --base)
      git rev-parse --verify --quiet "$REF" || {
        echo "no baseline set; run --mark to set one" >&2
        exit 1
      }
      exit 0 ;;
    --files) files_only=1 ;;
    --include-wip|--dirty) include_wip=1 ;;
    -h|--help) show_help; exit 0 ;;
    *) echo "unknown argument: $arg" >&2; show_help >&2; exit 2 ;;
  esac
done

base=$(git rev-parse --verify --quiet "$REF" \
       || git rev-list --max-parents=0 HEAD | tail -1)

# With --include-wip, omit the second ref so git diffs working tree.
if (( include_wip )); then
  end=()
else
  end=("HEAD")
fi

if (( files_only )); then
  git diff --name-only "$base" "${end[@]}"
else
  git diff "$base" "${end[@]}"
fi
