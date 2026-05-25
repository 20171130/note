#!/usr/bin/env bash
# Tools for the learner — review repo changes since the last scan, mark the
# new baseline, and sync the baseline + notes across machines.
#
# Baseline is stored in the git branch `learner-baseline` so it propagates via
# push/pull. If unset, falls back to the root commit (everything is new).
#
# Usage:
#   learn.sh status                                show baseline, unscanned count, working tree, ahead/behind
#   learn.sh diff [--name-only] [--include-wip]   show changes since last scan
#   learn.sh mark                                  record HEAD as scanned
#   learn.sh base                                  print the current baseline commit
#   learn.sh pull                                  pull current branch + learner-baseline from origin
#   learn.sh push                                  push current branch + learner-baseline to origin
#   learn.sh possess                               regenerate Devmate/Claude at $HOME and Cursor at repo
#   learn.sh sync                                  pull; if remote had updates stop, else mark + push + possess
#   learn.sh commit [git commit args...]           git commit as Galatea (--amend/--reset-author forbidden)
#   learn.sh help                                  show this help

set -euo pipefail

REF="refs/heads/learner-baseline"
BRANCH="learner-baseline"
REMOTE="origin"
GALATEA_NAME="Galatea"
GALATEA_EMAIL="galatea@bi.local"

cd "$(git rev-parse --show-toplevel)"
REPO_ROOT=$(git rev-parse --show-toplevel)
POSSESS="$REPO_ROOT/.agent/skills/possess/scripts/possess.py"

show_help() { sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; }

current_branch() { git rev-parse --abbrev-ref HEAD; }
baseline_commit() { git rev-parse --verify --quiet "$REF" || true; }

cmd_diff() {
  local files_only=0 include_wip=0
  for arg in "$@"; do
    case "$arg" in
      --name-only|--files) files_only=1 ;;
      --include-wip|--dirty) include_wip=1 ;;
      *) echo "diff: unknown arg: $arg" >&2; return 2 ;;
    esac
  done
  local base
  base=$(baseline_commit)
  [[ -n "$base" ]] || base=$(git rev-list --max-parents=0 HEAD | tail -1)
  local end=()
  (( include_wip )) || end=("HEAD")
  if (( files_only )); then
    git diff --name-only "$base" "${end[@]}"
  else
    git diff "$base" "${end[@]}"
  fi
}

cmd_mark() {
  git update-ref "$REF" "$(git rev-parse HEAD)"
  echo "marked $(git rev-parse --short HEAD) as scanned (branch learner-baseline)" >&2
}

cmd_base() {
  local b
  b=$(baseline_commit)
  if [[ -n "$b" ]]; then
    echo "$b"
  else
    echo "no baseline set; run \`learn.sh mark\` to set one" >&2
    return 1
  fi
}

short_commit() { [[ -n "$1" ]] && git rev-parse --short "$1" || echo "(unset)"; }

cmd_status() {
  local cur head_short baseline_short unscanned working ahead behind upstream
  local unstaged=0 staged=0
  cur=$(current_branch)
  head_short=$(git rev-parse --short HEAD)
  baseline_short=$(short_commit "$(baseline_commit)")
  if [[ "$baseline_short" != "(unset)" ]]; then
    unscanned=$(git rev-list --count "$REF..HEAD")
  else
    unscanned="all (no baseline)"
  fi
  git diff --quiet --ignore-submodules || unstaged=1
  git diff --cached --quiet --ignore-submodules || staged=1
  if (( unstaged && staged )); then working="unstaged + staged changes"
  elif (( unstaged )); then working="unstaged changes"
  elif (( staged )); then working="staged changes"
  else working="clean"
  fi
  upstream="$REMOTE/$cur"
  if git rev-parse --verify --quiet "$upstream" >/dev/null; then
    ahead=$(git rev-list --count "$upstream..HEAD")
    behind=$(git rev-list --count "HEAD..$upstream")
    printf 'branch:    %s (ahead %s, behind %s vs %s)\n' "$cur" "$ahead" "$behind" "$upstream"
  else
    printf 'branch:    %s (no upstream)\n' "$cur"
  fi
  printf 'HEAD:      %s\n' "$head_short"
  printf 'baseline:  %s\n' "$baseline_short"
  printf 'unscanned: %s commits\n' "$unscanned"
  printf 'working:   %s\n' "$working"
}

cmd_pull() {
  local cur
  cur=$(current_branch)
  echo "pulling $cur from $REMOTE..." >&2
  if ! git pull --ff-only "$REMOTE" "$cur"; then
    echo "pull: $cur cannot fast-forward (local commits diverge from $REMOTE/$cur); rebase or merge manually, then retry" >&2
    return 1
  fi
  if git ls-remote --exit-code --heads "$REMOTE" "$BRANCH" >/dev/null 2>&1; then
    if [[ "$cur" == "$BRANCH" ]]; then
      echo "$BRANCH already updated (it is the current branch)" >&2
    else
      echo "fast-forwarding $BRANCH..." >&2
      if ! git fetch "$REMOTE" "$BRANCH:$BRANCH"; then
        echo "pull: $BRANCH cannot fast-forward (was it reset on $REMOTE?); resolve manually with git fetch +$BRANCH:$BRANCH if you want to overwrite local" >&2
        return 1
      fi
    fi
  else
    echo "$REMOTE has no $BRANCH yet; skipping" >&2
  fi
}

cmd_push() {
  local cur
  cur=$(current_branch)
  echo "pushing $cur to $REMOTE..." >&2
  git push "$REMOTE" "$cur"
  if [[ -n "$(baseline_commit)" ]]; then
    echo "pushing $BRANCH to $REMOTE..." >&2
    git push "$REMOTE" "$BRANCH"
  else
    echo "no local $BRANCH; skipping" >&2
  fi
}

cmd_possess() {
  echo "possessing Devmate + Claude at $HOME..." >&2
  python3 "$POSSESS" --target "$HOME" --devmate --claude sync
  echo "possessing Cursor at $REPO_ROOT..." >&2
  python3 "$POSSESS" --target "$REPO_ROOT" --cursor sync
}

# sync = pull, then either:
#   - stop if the pull brought *unreviewed* commits (HEAD advanced past the
#     baseline), so the critic can review them; or
#   - proceed with mark + push + possess (no-ops when nothing changed; only
#     the possess does real work in the "remote-already-consolidated" case
#     where another Galatea-instance marked through the new HEAD).
cmd_sync() {
  local head_before head_after baseline_after base_for_count n
  head_before=$(git rev-parse HEAD)
  cmd_pull
  head_after=$(git rev-parse HEAD)
  baseline_after=$(baseline_commit)
  if [[ "$head_before" != "$head_after" && "$head_after" != "$baseline_after" ]]; then
    base_for_count="${baseline_after:-$(git rev-list --max-parents=0 HEAD | tail -1)}"
    n=$(git rev-list --count "$base_for_count..HEAD")
    echo "sync: pulled $n unreviewed commit(s) past baseline $(short_commit "$baseline_after"); review with \`learn.sh diff\` then rerun \`learn.sh sync\`" >&2
    return 1
  fi
  cmd_mark
  cmd_push
  cmd_possess
  echo "sync: complete" >&2
}

# Galatea-authored commit: identity scoped to this script so the repo's default
# user stays whatever the user configured globally. Forwards all remaining args
# to git commit (e.g. -m "...", -a). History-rewriting flags are rejected; use
# plain `git commit --amend` explicitly when you really intend to rewrite.
cmd_commit() {
  for arg in "$@"; do
    case "$arg" in
      --amend|--reset-author)
        echo "learn.sh commit: $arg is forbidden; run plain \`git commit $arg\` explicitly when you intend to rewrite history" >&2
        return 2 ;;
    esac
  done
  git -c "user.name=$GALATEA_NAME" -c "user.email=$GALATEA_EMAIL" commit "$@"
}

sub=${1:-help}
shift || true
case "$sub" in
  status) cmd_status ;;
  diff) cmd_diff "$@" ;;
  mark) cmd_mark ;;
  base) cmd_base ;;
  pull) cmd_pull ;;
  push) cmd_push ;;
  possess) cmd_possess ;;
  sync) cmd_sync ;;
  commit) cmd_commit "$@" ;;
  help|-h|--help) show_help ;;
  *) echo "unknown subcommand: $sub" >&2; show_help >&2; exit 2 ;;
esac
