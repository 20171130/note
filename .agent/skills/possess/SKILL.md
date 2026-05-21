---
name: possess
description: Sync canonical .agent customizations into Devmate, Claude, and Cursor formats.
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
For Devmate and Claude, target should be user home.
Cursor does not support user level rules (which in configurated via Cursor IDE GUI), so need to target each project repo separately.

Derived targets:

- Devmate: `<target>/.llms/rules/*.md` and `<target>/.llms/skills/<name>/SKILL.md`
- Cursor: `<target>/.cursor/rules/*.mdc` and `<target>/.cursor/skills/<name>/SKILL.md`
- Claude: `<target>/.claude/CLAUDE.md` and `<target>/.claude/commands/*.md`
- OpenClaw: not supported yet

It works on both windows and *nix.
Skill `scripts/` subdirectories and sibling `*.py` files are copied alongside the SKILL.md for Devmate and Cursor.

# .agent rule DSL

Rules use Markdown with YAML frontmatter:

```yaml
---
description: Writing style for text documents
alwaysApply: true
include_rule:
  - ./core.mdc
  - ./reasoning.mdc
---
```

`description` is emitted to generated formats that support descriptions.

`alwaysApply: true` marks a rule as global. Global rules are generated as top-level Devmate, Cursor, and Claude rules.

`include_rule` Both rules and skills can include rules. Included non-global rules are inlined before the including rule body in depth-first order.

Paths in `include_rule` are relative to the rule file that declares them.

Rules included through multiple routes are deduplicated by resolved source path within each generated output. Recursive includes are skipped once already seen.
