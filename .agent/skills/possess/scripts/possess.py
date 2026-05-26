#!/usr/bin/env python3
"""Derive assistant-specific customization files from a canonical .agent tree.

.agent is the source DSL. Rules are Markdown files with `description`,
Cursor's `alwaysApply`, and the portable `include_rule` list.
Skills are directories under .agent/skills/<name>/ containing SKILL.md (and
optionally a scripts/ subdirectory). Both rules and skills may carry
`include_rule`; included non-global rules are inlined depth-first before the
including body.

All outputs are written under a single project root (the `--target` flag,
defaulting to the parent of the .agent source). Cursor does not support
user-level file-based rules, so per-project layout is the canonical convention
for every target:

  <target>/.llms/rules/*.md, <target>/.llms/skills/<name>/, and
      <target>/.llms/commands/<name>.md   (Devmate; location is the always-apply
      signal, so `alwaysApply` is omitted; skill bodies are also emitted as
      slash commands).
  <target>/.cursor/rules/*.mdc and <target>/.cursor/skills/<name>/   (Cursor;
      `description` and `alwaysApply` preserved on rules, .agent-only fields
      such as `include_rule` stripped; .md is renamed to .mdc since Cursor
      requires that extension).
  <target>/.claude/CLAUDE.md plus <target>/.claude/commands/*.md   (Claude;
      rule bodies consolidated into one file, skill bodies become commands).
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
RULE_LINK_RE = re.compile(r"\]\(\.\./\.\./rules/([^)#]+)\.md(#[-A-Za-z0-9_]+)?\)")


def default_source() -> Path:
    for parent in Path(__file__).resolve().parents:
        if parent.name == ".agent":
            return parent
    return Path.cwd().resolve()


PLATFORMS = ("devmate", "cursor", "claude")


@dataclass(frozen=True)
class Config:
    target: Path
    source: Path
    devmate: Path
    cursor: Path
    claude: Path
    platforms: frozenset[str]

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "Config":
        source = (
            Path(args.source).expanduser().resolve()
            if args.source
            else default_source()
        )
        target = (
            Path(args.target).expanduser().resolve() if args.target else source.parent
        )
        selected = {p for p in PLATFORMS if getattr(args, p)}
        if args.all or not selected:
            selected = set(PLATFORMS)
        return cls(
            target=target,
            source=source,
            devmate=target / ".llms",
            cursor=target / ".cursor",
            claude=target / ".claude",
            platforms=frozenset(selected),
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
            data[key] = value.strip("\"'")
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


def rules(source: Path) -> list[Path]:
    return sorted((source / "rules").glob("*.md"))


def skills(source: Path) -> list[Path]:
    skills_dir = source / "skills"
    if not skills_dir.exists():
        return []
    return sorted(
        path for path in skills_dir.iterdir() if (path / "SKILL.md").is_file()
    )


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
    bodies = [body for _, body in expanded_rule_parts(path, set())]
    lines.append("\n\n".join(bodies))
    return "\n".join(lines).rstrip() + "\n"


def devmate_rule_as_skill_content(path: Path) -> str:
    data = parse_frontmatter(read_text(path))
    lines = ["---", f"name: {path.stem}"]
    if "description" in data:
        lines.append(f"description: {data['description']}")
    lines.extend(["---", ""])
    bodies = [body for _, body in expanded_rule_parts(path, set())]
    lines.append("\n\n".join(bodies))
    return "\n".join(lines).rstrip() + "\n"


def filter_frontmatter_lines(frontmatter: str, drop_keys: set[str]) -> str:
    out: list[str] = []
    drop_active = False
    for raw_line in frontmatter.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            drop_active = False
            out.append(line)
            continue
        if line.startswith(" ") and drop_active:
            continue
        key, sep, _ = line.partition(":")
        if sep and not line.startswith(" ") and key.strip() in drop_keys:
            drop_active = True
            continue
        drop_active = False
        out.append(line)
    return "\n".join(out).rstrip()


def skill_content(skill_path: Path) -> str:
    frontmatter_src, _ = split_frontmatter(read_text(skill_path))
    filtered = filter_frontmatter_lines(frontmatter_src, {"include_rule"})
    bodies = [body for _, body in expanded_rule_parts(skill_path, set())]
    lines = ["---"]
    if filtered:
        lines.append(filtered)
    lines.extend(["---", ""])
    lines.append("\n\n".join(bodies))
    return "\n".join(lines).rstrip() + "\n"


def devmate_command_content(skill_path: Path) -> str:
    data = parse_frontmatter(read_text(skill_path))
    name = skill_path.parent.name
    display_name = name.replace("_", " ").replace("-", " ").title()
    lines = ["---", f"displayName: {display_name}"]
    if "description" in data:
        lines.append(f"description: {data['description']}")
    lines.extend(["---", ""])
    bodies = [body for _, body in expanded_rule_parts(skill_path, set())]
    lines.append("\n\n".join(bodies))
    return "\n".join(lines).rstrip() + "\n"


def claude_command_content(skill_path: Path) -> str:
    bodies = [body for _, body in expanded_rule_parts(skill_path, set())]
    body = "\n\n".join(bodies)
    return rewrite_skill_links_for_claude(body)


def build_claude_rules(rule_files: Iterable[Path]) -> str:
    parts = [
        "# Agent Rules",
        "",
        "Generated from canonical rules in `~/note/.agent/rules`. Edit the source files, not this file.",
        "",
    ]
    for path in rule_files:
        parts.extend([f"## {path.stem}", ""])
        for part_path, body in expanded_rule_parts(path, set()):
            if part_path != path:
                parts.extend([f"### {part_path.stem}", ""])
            parts.extend([body, ""])
    return "\n".join(parts).rstrip() + "\n"


def sync(config: Config, dry_run: bool) -> list[str]:
    if not config.source.exists():
        raise FileNotFoundError(f"source directory does not exist: {config.source}")

    changed: list[str] = []
    expected_files: set[Path] = set()
    do_devmate = "devmate" in config.platforms
    do_cursor = "cursor" in config.platforms
    do_claude = "claude" in config.platforms

    for rule in rules(config.source):
        is_global = parse_frontmatter(read_text(rule)).get("alwaysApply") is True
        if do_devmate:
            if is_global:
                devmate_target = config.devmate / "rules" / f"{rule.stem}.md"
                devmate_text = devmate_rule_content(rule)
            else:
                devmate_target = config.devmate / "skills" / rule.stem / "SKILL.md"
                devmate_text = devmate_rule_as_skill_content(rule)
            expected_files.add(devmate_target)
            if atomic_write(devmate_target, devmate_text, dry_run):
                changed.append(str(devmate_target))
        if do_cursor:
            cursor_target = config.cursor / "rules" / f"{rule.stem}.mdc"
            expected_files.add(cursor_target)
            if atomic_write(cursor_target, cursor_rule_content(rule), dry_run):
                changed.append(str(cursor_target))

    if do_claude:
        claude_rule_target = config.claude / "CLAUDE.md"
        expected_files.add(claude_rule_target)
        if atomic_write(
            claude_rule_target, build_claude_rules(rules(config.source)), dry_run
        ):
            changed.append(str(claude_rule_target))

    for skill_dir in skills(config.source):
        skill_name = skill_dir.name
        source_skill = skill_dir / "SKILL.md"
        skill_text = skill_content(source_skill) if (do_devmate or do_cursor) else ""

        if do_devmate:
            devmate_skill = config.devmate / "skills" / skill_name / "SKILL.md"
            expected_files.add(devmate_skill)
            if atomic_write(devmate_skill, skill_text, dry_run):
                changed.append(str(devmate_skill))
            devmate_command = config.devmate / "commands" / f"{skill_name}.md"
            expected_files.add(devmate_command)
            if atomic_write(
                devmate_command, devmate_command_content(source_skill), dry_run
            ):
                changed.append(str(devmate_command))
        if do_cursor:
            cursor_skill = config.cursor / "skills" / skill_name / "SKILL.md"
            expected_files.add(cursor_skill)
            if atomic_write(cursor_skill, skill_text, dry_run):
                changed.append(str(cursor_skill))
        if do_claude:
            claude_command = config.claude / "commands" / f"{skill_name}.md"
            expected_files.add(claude_command)
            if atomic_write(
                claude_command, claude_command_content(source_skill), dry_run
            ):
                changed.append(str(claude_command))

        scripts_dir = skill_dir / "scripts"
        scripts_targets: list[Path] = []
        if do_devmate:
            scripts_targets.append(config.devmate / "skills" / skill_name / "scripts")
        if do_cursor:
            scripts_targets.append(config.cursor / "skills" / skill_name / "scripts")
        if scripts_dir.exists():
            for src_file in scripts_dir.rglob("*"):
                if src_file.is_file():
                    rel = src_file.relative_to(scripts_dir)
                    for target_scripts in scripts_targets:
                        expected_files.add(target_scripts / rel)
            for target_scripts in scripts_targets:
                if tree_fingerprint(scripts_dir) != tree_fingerprint(target_scripts):
                    changed.append(str(target_scripts))
                    if not dry_run:
                        if target_scripts.exists():
                            shutil.rmtree(target_scripts)
                        shutil.copytree(scripts_dir, target_scripts)

        skill_targets: list[Path] = []
        if do_devmate:
            skill_targets.append(config.devmate / "skills" / skill_name)
        if do_cursor:
            skill_targets.append(config.cursor / "skills" / skill_name)
        for py_file in sorted(skill_dir.glob("*.py")):
            for target_skill in skill_targets:
                target_py = target_skill / py_file.name
                expected_files.add(target_py)
                if (
                    not target_py.exists()
                    or py_file.read_bytes() != target_py.read_bytes()
                ):
                    changed.append(str(target_py))
                    if not dry_run:
                        target_skill.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(py_file, target_py)

    managed_roots: list[Path] = []
    if do_devmate:
        managed_roots.extend([
            config.devmate / "rules",
            config.devmate / "skills",
            config.devmate / "commands",
        ])
    if do_cursor:
        managed_roots.extend([config.cursor / "rules", config.cursor / "skills"])
    if do_claude:
        managed_roots.append(config.claude / "commands")
    changed.extend(cleanup(managed_roots, expected_files, dry_run))

    return changed


def cleanup(roots: list[Path], expected_files: set[Path], dry_run: bool) -> list[str]:
    removed: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path not in expected_files:
                removed.append(f"deleted {path}")
                if not dry_run:
                    path.unlink()
        for path in sorted(root.rglob("*"), key=lambda p: -len(p.parts)):
            if path.is_dir() and not any(path.iterdir()):
                removed.append(f"deleted {path}")
                if not dry_run:
                    path.rmdir()
    return removed


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
    print(f"target: {config.target}")
    print(f"source: {config.source}")
    print(f"platforms: {', '.join(sorted(config.platforms))}")
    if "devmate" in config.platforms:
        print(f"devmate: {config.devmate}")
    if "cursor" in config.platforms:
        print(f"cursor: {config.cursor}")
    if "claude" in config.platforms:
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
    parser.add_argument(
        "--target",
        help="Output root; user home for Devmate/Claude, project repo for Cursor. Defaults to the parent of the .agent source.",
    )
    parser.add_argument(
        "--source",
        help="Canonical .agent source directory; defaults to the .agent ancestor of this script.",
    )
    parser.add_argument(
        "--devmate", action="store_true", help="Include Devmate output."
    )
    parser.add_argument("--cursor", action="store_true", help="Include Cursor output.")
    parser.add_argument("--claude", action="store_true", help="Include Claude output.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include all platforms (default if no platform flag is given).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="Preview generated paths without writing.")
    subparsers.add_parser("sync", help="Generate assistant-specific files.")
    watch = subparsers.add_parser(
        "watch", help="Poll the source tree and sync on changes."
    )
    watch.add_argument(
        "--interval", type=float, default=2.0, help="Polling interval in seconds."
    )
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
