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
#   learn.sh --pull          pull current branch + learner-baseline from origin
#   learn.sh --push          mark HEAD, push current branch + learner-baseline, then possess
#   learn.sh -h | --help     show this help

set -euo pipefail

REF="refs/heads/learner-baseline"
BRANCH="learner-baseline"
REMOTE="origin"
cd "$(git rev-parse --show-toplevel)"

show_help() { sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; }

REPO_ROOT=$(git rev-parse --show-toplevel)
POSSESS="$REPO_ROOT/.agent/skills/possess/scripts/possess.py"

current_branch() { git rev-parse --abbrev-ref HEAD; }

do_pull() {
  local cur
  cur=$(current_branch)
  echo "fetching $REMOTE..." >&2
  git fetch "$REMOTE"
  echo "fast-forwarding $cur..." >&2
  git pull --ff-only "$REMOTE" "$cur"
  if git ls-remote --exit-code --heads "$REMOTE" "$BRANCH" >/dev/null 2>&1; then
    if [[ "$cur" == "$BRANCH" ]]; then
      echo "$BRANCH already updated (it is the current branch)" >&2
    else
      echo "fast-forwarding $BRANCH..." >&2
      git fetch "$REMOTE" "$BRANCH:$BRANCH"
    fi
  else
    echo "$REMOTE has no $BRANCH yet; skipping" >&2
  fi
}

do_mark() {
  git update-ref "$REF" "$(git rev-parse HEAD)"
  echo "marked $(git rev-parse --short HEAD) as scanned (branch learner-baseline)" >&2
}

do_push() {
  local cur
  cur=$(current_branch)
  do_mark
  echo "pushing $cur to $REMOTE..." >&2
  git push "$REMOTE" "$cur"
  echo "pushing $BRANCH to $REMOTE..." >&2
  git push "$REMOTE" "$BRANCH"
  echo "possessing Devmate + Claude at $HOME..." >&2
  python3 "$POSSESS" --target "$HOME" --devmate --claude sync
  echo "possessing Cursor at $REPO_ROOT..." >&2
  python3 "$POSSESS" --target "$REPO_ROOT" --cursor sync
}

files_only=0
include_wip=0
for arg in "$@"; do
  case "$arg" in
    --mark)
      do_mark
      echo "push with: learn.sh --push" >&2
      exit 0 ;;
    --base)
      git rev-parse --verify --quiet "$REF" || {
        echo "no baseline set; run --mark to set one" >&2
        exit 1
      }
      exit 0 ;;
    --pull) do_pull; exit 0 ;;
    --push) do_push; exit 0 ;;
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
