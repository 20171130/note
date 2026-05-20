#!/usr/bin/env python3
"""Derive assistant-specific customization files from a canonical .agent tree.

.agent is the source DSL. Rules are Cursor-compatible .mdc files with
`description`, Cursor's `alwaysApply`, and the portable `include_rule` list.
`include_rule` is expanded depth-first for targets that need inlined context.

Devmate uses ~/.llms/rules/*.md: location is the always-apply signal, so
`alwaysApply` is omitted and .mdc is converted to .md. Cursor uses
~/.cursor/rules/*.mdc: `description` and `alwaysApply` are preserved, while
.agent-only fields such as `include_rule` are stripped. Claude uses one global
~/.claude/CLAUDE.md plus command files, so rule bodies are consolidated and
skill bodies become ~/.claude/commands/*.md.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
RULE_LINK_RE = re.compile(r"\]\(\.\./\.\./rules/([^)#]+)\.mdc(#[-A-Za-z0-9_]+)?\)")


def default_source() -> Path:
    for parent in Path(__file__).resolve().parents:
        if parent.name == ".agent":
            return parent
    return Path.cwd().resolve()


@dataclass(frozen=True)
class Config:
    home: Path
    source: Path
    devmate: Path
    cursor: Path
    claude: Path

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "Config":
        home = Path(args.home).expanduser().resolve() if args.home else Path.home().resolve()
        source = Path(args.source).expanduser().resolve() if args.source else default_source()
        return cls(
            home=home,
            source=source,
            devmate=home / ".llms",
            cursor=home / ".cursor",
            claude=home / ".claude",
        )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_frontmatter(text: str) -> tuple[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return "", text
    return match.group(1), text[match.end() :]


def strip_frontmatter(text: str) -> str:
    return split_frontmatter(text)[1].lstrip()


def parse_frontmatter(text: str) -> dict[str, object]:
    frontmatter, _ = split_frontmatter(text)
    data: dict[str, object] = {}
    current_list: str | None = None
    for raw_line in frontmatter.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.startswith("  - ") and current_list:
            value = line[4:].strip()
            data[current_list].append(value)
            continue
        current_list = None
        key, sep, value = line.partition(":")
        if not sep:
            continue
        key = key.strip()
        value = value.strip()
        if value == "":
            data[key] = []
            current_list = key
        elif value.lower() == "true":
            data[key] = True
        elif value.lower() == "false":
            data[key] = False
        else:
            data[key] = value.strip('"\'')
    return data


def cursor_rule_content(path: Path) -> str:
    data = parse_frontmatter(read_text(path))
    body = strip_frontmatter(read_text(path))
    lines = ["---"]
    if "description" in data:
        lines.append(f"description: {data['description']}")
    if data.get("alwaysApply") is True:
        lines.append("alwaysApply: true")
    lines.extend(["---", "", body.lstrip()])
    return "\n".join(lines)


def ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def rewrite_skill_links_for_claude(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        rule_name = match.group(1)
        section = match.group(2) or ""
        anchor = section.lower() if section else ""
        return f"](CLAUDE.md#{rule_name}{anchor})"

    return RULE_LINK_RE.sub(replace, text)


def atomic_write(path: Path, content: str, dry_run: bool) -> bool:
    content = ensure_trailing_newline(content)
    if path.exists() and read_text(path) == content:
        return False
    if dry_run:
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)
    return True


def copy_file(source: Path, target: Path, dry_run: bool) -> bool:
    content = read_text(source)
    return atomic_write(target, content, dry_run)


def write_generated(content: str, target: Path, dry_run: bool) -> bool:
    return atomic_write(target, content, dry_run)


def rules(source: Path) -> list[Path]:
    return sorted((source / "rules").glob("*.mdc"))


def skills(source: Path) -> list[Path]:
    skills_dir = source / "skills"
    if not skills_dir.exists():
        return []
    return sorted(path for path in skills_dir.iterdir() if (path / "SKILL.md").is_file())


def included_rule_paths(path: Path) -> list[Path]:
    data = parse_frontmatter(read_text(path))
    include_rule = data.get("include_rule", [])
    if isinstance(include_rule, str):
        include_rule = [include_rule]
    return [(path.parent / str(include)).resolve() for include in include_rule]


def expanded_rule_parts(path: Path, seen: set[Path]) -> list[tuple[Path, str]]:
    path = path.resolve()
    if path in seen:
        return []
    seen.add(path)
    data = parse_frontmatter(read_text(path))
    parts: list[tuple[Path, str]] = []
    for included in included_rule_paths(path):
        if parse_frontmatter(read_text(included)).get("alwaysApply") is not True:
            parts.extend(expanded_rule_parts(included, seen))
    body = strip_frontmatter(read_text(path)).strip()
    parts.append((path, body))
    return parts


def devmate_rule_content(path: Path) -> str:
    data = parse_frontmatter(read_text(path))
    lines = ["---"]
    if "description" in data:
        lines.append(f"description: {data['description']}")
    lines.extend(["---", ""])
    for part_path, body in expanded_rule_parts(path, set()):
        if part_path != path:
            lines.extend([f"# {part_path.stem}", ""])
        lines.extend([body, ""])
    return "\n".join(lines).rstrip() + "\n"


def build_claude_rules(rule_files: Iterable[Path]) -> str:
    parts = [
        "# Agent Rules",
        "",
        "Generated from canonical rules in `~/note/.agent/rules`. Edit the source files, not this file.",
        "",
    ]
    for path in rule_files:
        name = path.stem
        parts.extend([f"## {name}", ""])
        for part_path, body in expanded_rule_parts(path, set()):
            if part_path != path:
                parts.extend([f"### {part_path.stem}", ""])
            parts.extend([body, ""])
    return "\n".join(parts).rstrip() + "\n"


def sync(config: Config, dry_run: bool) -> list[str]:
    if not config.source.exists():
        raise FileNotFoundError(f"source directory does not exist: {config.source}")

    changed: list[str] = []

    for rule in rules(config.source):
        devmate_target = config.devmate / "rules" / f"{rule.stem}.md"
        cursor_target = config.cursor / "rules" / rule.name
        if write_generated(devmate_rule_content(rule), devmate_target, dry_run):
            changed.append(str(devmate_target))
        if write_generated(cursor_rule_content(rule), cursor_target, dry_run):
            changed.append(str(cursor_target))

    claude_rules = build_claude_rules(rules(config.source))
    claude_rule_target = config.claude / "CLAUDE.md"
    if atomic_write(claude_rule_target, claude_rules, dry_run):
        changed.append(str(claude_rule_target))

    for skill_dir in skills(config.source):
        skill_name = skill_dir.name
        source_skill = skill_dir / "SKILL.md"
        devmate_skill = config.devmate / "skills" / skill_name / "SKILL.md"
        claude_command = config.claude / "commands" / f"{skill_name}.md"

        if copy_file(source_skill, devmate_skill, dry_run):
            changed.append(str(devmate_skill))

        claude_body = rewrite_skill_links_for_claude(strip_frontmatter(read_text(source_skill)))
        if atomic_write(claude_command, claude_body, dry_run):
            changed.append(str(claude_command))

        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists():
            target_scripts = config.devmate / "skills" / skill_name / "scripts"
            if tree_fingerprint(scripts_dir) != tree_fingerprint(target_scripts):
                changed.append(str(target_scripts))
                if not dry_run:
                    if target_scripts.exists():
                        shutil.rmtree(target_scripts)
                    shutil.copytree(scripts_dir, target_scripts)

    return changed


def tree_fingerprint(source: Path) -> str:
    digest = hashlib.sha256()
    if not source.exists():
        return "missing"
    for path in sorted(p for p in source.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(source)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def source_fingerprint(source: Path) -> str:
    return tree_fingerprint(source)


def print_config(config: Config) -> None:
    print(f"home: {config.home}")
    print(f"source: {config.source}")
    print(f"devmate: {config.devmate}")
    print(f"cursor: {config.cursor}")
    print(f"claude: {config.claude}")


def command_check(config: Config) -> int:
    print_config(config)
    changed = sync(config, dry_run=True)
    if changed:
        print("pending changes:")
        for path in changed:
            print(f"  {path}")
    else:
        print("pending changes: none")
    return 0


def command_sync(config: Config) -> int:
    changed = sync(config, dry_run=False)
    if changed:
        print("updated:")
        for path in changed:
            print(f"  {path}")
    else:
        print("already up to date")
    return 0


def command_watch(config: Config, interval: float) -> int:
    print_config(config)
    print(f"watching every {interval:g}s; press Ctrl-C to stop")
    last = None
    try:
        while True:
            current = source_fingerprint(config.source)
            if current != last:
                changed = sync(config, dry_run=False)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                if changed:
                    print(f"[{timestamp}] synced {len(changed)} paths")
                elif last is None:
                    print(f"[{timestamp}] already up to date")
                last = current
            time.sleep(interval)
    except KeyboardInterrupt:
        print("stopped")
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", help="Home directory for generated global config; defaults to Path.home().")
    parser.add_argument("--source", help="Canonical .agent source directory; defaults to ~/note/.agent.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="Preview generated paths without writing.")
    subparsers.add_parser("sync", help="Generate assistant-specific files.")
    watch = subparsers.add_parser("watch", help="Poll the source tree and sync on changes.")
    watch.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds.")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    config = Config.from_args(args)
    if args.command == "check":
        return command_check(config)
    if args.command == "sync":
        return command_sync(config)
    if args.command == "watch":
        return command_watch(config, args.interval)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
