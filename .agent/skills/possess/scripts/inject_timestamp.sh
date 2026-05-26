#!/usr/bin/env bash
# Devmate hook: inject the current timestamp in Henry's timezone as additionalContext.
# Fixes the recurring actor failure mode where env_details' UTC timestamp gets
# mis-labeled "PDT". Wired on SessionStart and UserPromptSubmit in ~/.llms/hooks.json.
set -u
TZ_PRIMARY='America/Los_Angeles'   # Henry's timezone — see note/.agent/rules/user.md
# Discard stdin (Devmate sends an event JSON we don't use here)
cat >/dev/null 2>&1
TS=$(TZ="$TZ_PRIMARY" date +'%Y-%m-%d %H:%M:%S %Z (%z)')
UTC=$(date -u +'%Y-%m-%d %H:%M:%S UTC')
# jq is overkill; emit a literal JSON object. additionalContext is the field
# Devmate (Claude-Code-compatible) wraps in a system-reminder for the next turn.
printf '{"additionalContext":"Current time — Henry'\''s timezone (%s): %s. UTC: %s. Use this, not env_details UTC, when timestamping logs."}\n' \
  "$TZ_PRIMARY" "$TS" "$UTC"
