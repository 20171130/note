# Heartbeat & Cron — Reference Notes

Reference material extracted from `galatea/AGENTS.md` per the conciseness rule. Principles stay in AGENTS.md; this file holds the worked example and the wake-source taxonomy.

## Worked Example: heartbeat task → scheduled cron

Suppose HEARTBEAT.md shows: `- [ ] Remind Henry to talk to Tom ⏳ 2026-05-18`
Henry says "Our meeting is scheduled for 17:15." I add a cron job:

```json
{
  "action": "add",
  "job": {
    "name": "Reminder: Meet with Tom",
    "schedule": {
      "kind": "at",
      "at": "2026-05-18T17:00:00",
      "tz": "America/Los_Angeles"
    },
    "payload": {
      "kind": "systemEvent",
      "text": "Remind Henry about his meeting with Tom at 17:15, and check HEARTBEAT.md for anything worth attention."
    },
    "sessionTarget": "main",
    "sessionKey": "agent:main:main",
    "wakeMode": "now",
    "deleteAfterRun": true
  }
}
```

Mark the heartbeat task in progress:
```
- [/] Remind Henry to talk to Tom ⏳ 2026-05-18
```
Remove it after confirming the meeting happened.

**Time zone:** Per USER.md (currently Bay Area) → `America/Los_Angeles`. OpenClaw resolves DST so I don't have to.

**Routing gotcha:** Discord DMs map to the main session, so the sessionKey is `agent:main:main`, not `agent:main:discord:...`.

**Replacing the next heartbeat tick:** Heartbeats are interval-from-last-run (next tick = 1h after my most recent main-session wake). A `wakeMode: "now"` cron counts as a wake — it resets the counter and replaces the next natural tick. So I append a heartbeat directive (e.g. "check HEARTBEAT.md for anything worth attention") to `systemEvent.text` so the single wake serves both purposes.

## Wake-source taxonomy

I'm woken by three sources, distinguished by the slot text and whether a `Conversation info (untrusted metadata):` block is appended:

| Source | Slot text | `Conversation info`? |
|---|---|---|
| Henry typing (Discord) | any text | **yes** |
| Heartbeat tick (framework wake) | literal `[OpenClaw heartbeat poll]` | no |
| My own cron firing | the cron's `systemEvent.text` | no |

In framework wakes (the latter two), the timestamp and HEARTBEAT.md content arrive in a separate `custom_message` turn beneath.

**Key rules to keep in mind without re-reading:**
- Discord DMs route to the main session - `sessionKey: "agent:main:main"`.
- Use IANA tz from USER.md so OpenClaw handles DST.
- A `wakeMode: "now"` cron replaces the next natural heartbeat tick, so append a heartbeat directive to `systemEvent.text` when the cron fires during heartbeat hours.