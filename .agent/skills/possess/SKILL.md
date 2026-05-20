---
name: possess
description: Sync canonical .agent customizations into Devmate, Claude, and Cursor formats.
---

# Possess

Use the containing `.agent` directory as the source of truth for agent rules and skills.

Run a one-shot sync:

```bash
python3 skills/possess/scripts/possess.py sync
```

Preview paths and pending changes without writing:

```bash
python3 skills/possess/scripts/possess.py check
```

Derived targets:

- Devmate: `~/.llms/rules/*.md` and `~/.llms/skills/<name>/SKILL.md`
- Cursor: `~/.cursor/rules/*.mdc`
- Claude: `~/.claude/CLAUDE.md` and `~/.claude/commands/*.md`

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

`include_rule` is only supported on rules. Included non-global rules are inlined before the including rule body in depth-first order.

Paths in `include_rule` are relative to the rule file that declares them.

Rules included through multiple routes are deduplicated by resolved source path within each generated output. Recursive includes are skipped once already seen.
