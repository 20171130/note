#!/usr/bin/env python3
"""Chat-driven paper recommender: Semantic Scholar (personalized) + HuggingFace trending.

State (`.recommender_state.json`) is a *buffer* of pending suggestions.
Each run by default:
  1. Auto-evicts entries whose paper now appears in `reading/` (status -> read).
  2. Fetches fresh candidates from S2 + HF and queues new ones.
  3. Prints the top --show queued entries to stdout for the agent to present.

Entries persist as `queued` until either:
  - The user creates a matching `reading/` note (auto-evicted as `read`), or
  - `--reject <id>` marks them rejected (also fed to S2 as negativePaperIds).

Output is plain markdown to stdout; no daily-log file is written. The agent
reads this output and surfaces a chat-sized selection.

Frontmatter DSL: see SKILL.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

S2_ENDPOINT = "https://api.semanticscholar.org/recommendations/v1/papers"
S2_FIELDS = "title,authors,year,venue,abstract,externalIds,url"
HF_ENDPOINT = "https://huggingface.co/api/daily_papers"
STATE_FILENAME = ".recommender_state.json"

ARXIV_RE = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?")


# --------------------------- frontmatter parser ---------------------------

def parse_frontmatter(text: str) -> dict:
    """Minimal YAML frontmatter parser. Supports `key: value` and `key: |` blocks."""
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    lines = text[4:end].splitlines()
    out: dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            i += 1
            continue
        key, _, rest = stripped.partition(":")
        key = key.strip()
        val = rest.strip()
        if val in ("|", ">"):
            i += 1
            base_indent: int | None = None
            content: list[str] = []
            while i < len(lines):
                ln = lines[i]
                if not ln.strip():
                    content.append("")
                    i += 1
                    continue
                indent = len(ln) - len(ln.lstrip())
                if base_indent is None:
                    base_indent = indent
                if indent < base_indent:
                    break
                content.append(ln[base_indent:])
                i += 1
            out[key] = "\n".join(content).rstrip("\n")
        else:
            if " #" in val:
                val = val.split(" #", 1)[0].rstrip()
            out[key] = val.strip().strip('"').strip("'")
            i += 1
    return out


def normalize_arxiv(raw: str) -> str | None:
    m = ARXIV_RE.search(raw)
    return m.group(1) if m else None


def find_note_root(start: Path) -> Path:
    for p in [start] + list(start.parents):
        if (p / "reading").is_dir() and (p / "log").is_dir():
            return p
    raise SystemExit(f"could not find note root above {start}")


# --------------------------- state ---------------------------

def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    today = dt.date.today().isoformat()
    if isinstance(raw, list):
        return {
            pid: {
                "first_seen": today,
                "status": "queued",
                "source": "hf" if pid.startswith("hf:") else "s2",
            }
            for pid in raw
        }
    for entry in raw.values():
        if entry.get("status") == "suggested":
            entry["status"] = "queued"
    return raw


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2, sort_keys=True))


def enqueue(state: dict, sid: str, source: str, paper: dict,
            arxiv: str | None = None, doi: str | None = None) -> bool:
    fields = {
        "title": paper.get("title"),
        "year": paper.get("year"),
        "url": paper.get("url"),
        "abstract": paper.get("abstract"),
        "arxiv": arxiv,
        "doi": doi,
    }
    if sid in state:
        entry = state[sid]
        for k, v in fields.items():
            if v and not entry.get(k):
                entry[k] = v
        return False
    state[sid] = {
        "first_seen": dt.date.today().isoformat(),
        "status": "queued",
        "source": source,
        **fields,
    }
    return True


def negative_seeds_from_state(state: dict) -> list[str]:
    negs: list[str] = []
    for sid, meta in state.items():
        if meta.get("status") != "rejected":
            continue
        if sid.startswith("hf:"):
            ax = sid[3:]
            if normalize_arxiv(ax):
                negs.append(f"ARXIV:{ax}")
        else:
            negs.append(sid)
    return negs


def mark_read_from_reading(state: dict, seeded_arxiv: set[str],
                            seeded_doi: set[str]) -> int:
    today = dt.date.today().isoformat()
    evicted = 0
    for meta in state.values():
        if meta.get("status") != "queued":
            continue
        ax = meta.get("arxiv")
        doi = meta.get("doi")
        if (ax and ax in seeded_arxiv) or (doi and doi in seeded_doi):
            meta["status"] = "read"
            meta["read_at"] = today
            evicted += 1
    return evicted


# --------------------------- collectors / fetchers ---------------------------

def collect_seeds(reading_dir: Path) -> tuple[list[str], set[str], set[str],
                                               list[Path]]:
    seeds: list[str] = []
    arxiv_ids: set[str] = set()
    doi_ids: set[str] = set()
    missing: list[Path] = []
    for md in sorted(reading_dir.rglob("*.md")):
        fm = parse_frontmatter(md.read_text(encoding="utf-8"))
        if fm.get("skip"):
            continue
        ax = normalize_arxiv(fm.get("arxiv", "")) if fm.get("arxiv") else None
        doi = fm.get("doi") if fm.get("doi") else None
        if ax:
            seeds.append(f"ARXIV:{ax}")
            arxiv_ids.add(ax)
        elif doi:
            seeds.append(f"DOI:{doi}")
            doi_ids.add(doi)
        else:
            missing.append(md)
    return seeds, arxiv_ids, doi_ids, missing


def fetch_recommendations(seeds: list[str], negatives: list[str],
                           limit: int) -> list[dict]:
    if not seeds:
        return []
    body = json.dumps({
        "positivePaperIds": seeds,
        "negativePaperIds": negatives,
    }).encode()
    url = f"{S2_ENDPOINT}?limit={limit}&fields={S2_FIELDS}"
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp).get("recommendedPapers", [])
    except urllib.error.HTTPError as e:
        print(f"S2 error {e.code}: {e.read().decode()}", file=sys.stderr)
        return []
    except urllib.error.URLError as e:
        print(f"S2 unreachable: {e}", file=sys.stderr)
        return []


def fetch_trending(limit: int) -> list[dict]:
    if limit <= 0:
        return []
    url = f"{HF_ENDPOINT}?limit={limit * 2}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.load(resp)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(f"HF unreachable: {e}", file=sys.stderr)
        return []


def ingest_s2(papers: list[dict], state: dict) -> int:
    added = 0
    for p in papers:
        pid = p.get("paperId")
        if not pid:
            continue
        ext = p.get("externalIds") or {}
        if enqueue(state, pid, "s2", p,
                   arxiv=ext.get("ArXiv"), doi=ext.get("DOI")):
            added += 1
    return added


def ingest_hf(items: list[dict], state: dict) -> int:
    added = 0
    for item in items:
        paper = item.get("paper", {})
        ax = paper.get("id", "")
        if not ax:
            continue
        sid = f"hf:{ax}"
        published = paper.get("publishedAt", "")
        year = int(published[:4]) if published[:4].isdigit() else None
        synthetic = {
            "title": paper.get("title"),
            "year": year,
            "url": f"https://arxiv.org/abs/{ax}",
            "abstract": paper.get("summary"),
        }
        if enqueue(state, sid, "hf", synthetic, arxiv=ax):
            added += 1
    return added


# --------------------------- display ---------------------------

def queued_entries(state: dict, source: str | None = None) -> list[tuple[str, dict]]:
    items = [(sid, m) for sid, m in state.items() if m.get("status") == "queued"]
    if source is not None:
        items = [it for it in items if it[1].get("source") == source]
    items.sort(
        key=lambda it: (-(it[1].get("year") or 0), it[1].get("first_seen", "")),
    )
    return items


def fmt_entry(sid: str, meta: dict) -> list[str]:
    title = meta.get("title") or "(no title)"
    url = meta.get("url")
    if not url and meta.get("arxiv"):
        url = f"https://arxiv.org/abs/{meta['arxiv']}"
    year = meta.get("year")
    abstract = (meta.get("abstract") or "").strip().replace("\n", " ")
    if len(abstract) > 280:
        abstract = abstract[:277] + "..."
    head = f"- [{title}]({url})" if url else f"- {title}"
    if year:
        head += f" — {year}"
    head += f"  `{sid}`"
    return [head, f"  {abstract}"] if abstract else [head]


def render_stdout(state: dict, s2_n: int, hf_n: int) -> None:
    s2_q = queued_entries(state, "s2")
    hf_q = queued_entries(state, "hf")
    print(f"## Personalized (Semantic Scholar) — {len(s2_q)} queued")
    print()
    if not s2_q:
        print("_queue empty_")
    for sid, meta in s2_q[:s2_n]:
        print("\n".join(fmt_entry(sid, meta)))
    if hf_n > 0:
        print()
        print(f"## Trending (HuggingFace daily) — {len(hf_q)} queued")
        print()
        if not hf_q:
            print("_queue empty_")
        for sid, meta in hf_q[:hf_n]:
            print("\n".join(fmt_entry(sid, meta)))


# --------------------------- commands ---------------------------

def cmd_reject(state_path: Path, ids: list[str]) -> int:
    state = load_state(state_path)
    today = dt.date.today().isoformat()
    for raw in ids:
        sid = raw
        if sid not in state:
            ax = normalize_arxiv(sid)
            if ax and f"hf:{ax}" in state:
                sid = f"hf:{ax}"
            else:
                print(f"warn: {raw} not in state; recording as rejected anyway",
                      file=sys.stderr)
                state[sid] = {
                    "first_seen": today, "status": "rejected",
                    "source": "manual",
                }
                continue
        state[sid]["status"] = "rejected"
        state[sid]["rejected_at"] = today
        print(f"rejected: {sid}  {state[sid].get('title') or ''}",
              file=sys.stderr)
    save_state(state_path, state)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--note-root", type=Path, default=None,
                        help="Repo root (default: walk up until reading/+log/)")
    parser.add_argument("--show", type=int, default=5,
                        help="S2 entries printed to stdout (default 5)")
    parser.add_argument("--trending", type=int, default=3,
                        help="HF entries printed to stdout (default 3; 0 disables)")
    parser.add_argument("--no-fetch", action="store_true",
                        help="Skip API calls; print from existing queue")
    parser.add_argument("--reject", nargs="+", metavar="ID",
                        help="Mark IDs as rejected and exit")
    args = parser.parse_args()

    state_path = Path(__file__).resolve().parent / STATE_FILENAME

    if args.reject:
        return cmd_reject(state_path, args.reject)

    root = args.note_root or find_note_root(Path(__file__).resolve().parent)
    reading_dir = root / "reading"

    seeds, arxiv_ids, doi_ids, missing = collect_seeds(reading_dir)
    state = load_state(state_path)
    evicted = mark_read_from_reading(state, arxiv_ids, doi_ids)

    s2_added = hf_added = 0
    if not args.no_fetch:
        negatives = negative_seeds_from_state(state)
        s2_added = ingest_s2(
            fetch_recommendations(seeds, negatives, limit=30), state,
        )
        hf_added = ingest_hf(fetch_trending(20), state)
        save_state(state_path, state)

    rejected_n = sum(1 for m in state.values() if m.get("status") == "rejected")
    read_n = sum(1 for m in state.values() if m.get("status") == "read")
    print(
        f"# {len(seeds)} seeds, {len(missing)} missing IDs, "
        f"{len(state)} total · read={read_n} rejected={rejected_n} "
        f"· +{s2_added}/+{hf_added} new · {evicted} auto-read"
        f"{' · no-fetch' if args.no_fetch else ''}",
        file=sys.stderr,
    )
    if missing:
        print("# Missing frontmatter IDs:", file=sys.stderr)
        for p in missing:
            print(f"  {p.relative_to(root).as_posix()}", file=sys.stderr)

    render_stdout(state, args.show, args.trending)
    return 0


if __name__ == "__main__":
    sys.exit(main())
