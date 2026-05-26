---
name: possess
description: Sync canonical `note/.agent/` rules and skills into Devmate, Claude, and Cursor
---

# Possess

Use the containing `.agent` directory as the source of truth for agent rules and skills.
User request example: "possess claude", "possess cursor (in this repo)".

Run a one-shot sync:

```bash
python3 skills/possess/scripts/possess.py  --target <target> sync
```

Preview paths and pending changes without writing:

```bash
python3 skills/possess/scripts/possess.py  --target <target> check
```

Use --devmate, --claude, --cursor or --all to specify application(s) to possess.

Derived targets:

- Devmate: `<target>/.llms/rules/*.md` and `<target>/.llms/skills/<name>/SKILL.md`
- Cursor: `<target>/.cursor/rules/*.mdc` and `<target>/.cursor/skills/<name>/SKILL.md`
- Claude: `<target>/.claude/CLAUDE.md` and `<target>/.claude/commands/*.md`
- OpenClaw: not supported yet

It works on both windows and *nix.
Skill `scripts/` subdirectories and sibling `*.py` files are copied alongside the SKILL.md for Devmate and Cursor.


# Devmate hooks

`scripts/inject_timestamp.sh` is a Devmate `SessionStart` + `UserPromptSubmit` [hook](https://www.internalfb.com/wiki/Devmate/Devmate_Hooks/) that injects the current time in Henry's timezone as `additionalContext` (fixes the recurring `env_details`-UTC-mistagged-as-PDT bug). After possess copies it to `~/.llms/skills/possess/scripts/`, wire it once in `~/.llms/hooks.json`:

```json
{
  "hooks": {
    "SessionStart":     [{"hooks": [{"type": "command", "command": "/home/hangrui/.llms/skills/possess/scripts/inject_timestamp.sh", "timeout": 5}]}],
    "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "/home/hangrui/.llms/skills/possess/scripts/inject_timestamp.sh", "timeout": 5}]}]
  }
}
```

`hooks.json` itself is not possessed — it's user-machine-specific (absolute paths). Restart Devmate to load.


# Different Specifications
For Devmate and Claude, target should be user home.
Cursor does not support user level rules (which in configurated via Cursor IDE GUI), so need to target each project repo separately.

Devmate does not support applying rules conditonally via glob matching (https://www.internalfb.com/wiki/Devmate/Devmate_Skills), unless via include_rule frontmatter of skills or other rules.
Therefore, conditional rules shoule be converted to skills for Devmate.


# .agent rule DSL

Rules use Markdown with YAML frontmatter:

```yaml
---
description: Writing style for text documents
alwaysApply: true
include_rule:
  - ./core.md
  - ./reasoning.md
---
```

`description` is emitted to generated formats that support descriptions.

`alwaysApply: true` marks a rule as global. Global rules are generated as top-level Devmate, Cursor, and Claude rules.

`include_rule` Both rules and skills can include rules. Included non-global rules are inlined before the including rule body in depth-first order.

Paths in `include_rule` are relative to the rule file that declares them.

Rules included through multiple routes are deduplicated by resolved source path within each generated output. Recursive includes are skipped once already seen.
