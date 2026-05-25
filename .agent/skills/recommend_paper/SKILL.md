---
name: recommend_paper
description: Chat-driven paper recommender. Invoke when user asks for paper suggestions, wants to reject a recommendation, or adds a new reading note.
---

# Paper Recommender

Daily paper discovery seeded by [`reading/`](/reading/) notes. The agent runs the script and presents a few picks in chat — no daily log file is written.

## Chat triggers

- _"Recommend papers" / "any new papers" / "what should I read"_ → run the script (fetches + ingests + prints top picks to stdout), pick the most relevant 2–3 to surface in chat, mention queue size.
- _"Reject X" / "skip that" / "not interested in the first one"_ → resolve X to a paper ID from the most recent suggestion (chat history), call `--reject`, confirm.
- _User mentions reading or being interested in a specific paper_ → create `reading/YYYY/<slug>.md` with frontmatter; the script auto-evicts from the buffer on next run.
- _"What's queued" / "show pending"_ → run with `--no-fetch` to print the current buffer without an API call.

## Reading-note frontmatter DSL

```yaml
---
title: UMA: A Family of Universal Models for Atoms   # required
arxiv: 2506.23971                                    # primary seed; v-suffix optional
doi:   10.1038/s41586-024-07487-w                    # alternative if no arxiv
skip:  boring                                        # boring | inaccessible | unindexed
bibtex: |                                            # optional, fill when citing
  @inproceedings{wood2025uma, ...}
---
```

`title:` required. At least one of `arxiv:` / `doi:` / `skip:` required. `arxiv:` wins over `doi:`.

## Sources

- Semantic Scholar Recommendations API[^s2_recs] — personalized from seeds; accepts `negativePaperIds` for rejected ones. Does **not** honour `year`/`publicationDateOrYear` filters on this endpoint (empirically silently ignored), so freshness depends on repeated fetches plus client-side year-desc sort.
- HuggingFace Daily Papers[^hf_daily] — editorially curated trending; complements S2's niche bias.

Because neither API exposes a time filter, the buffer only contains literature that existed during past fetches. Chat invocation is the fetch trigger; if you go a long stretch without chatting, the queue staleness is bounded by your next chat. (A future day-planner agent may schedule background refreshes.)

## State — `scripts/.recommender_state.json` (git-tracked)

Persistent buffer. Each entry: `{first_seen, status, source, title, year, url, abstract, arxiv, doi}`.

Status transitions: `queued` (default) → `read` (auto when a matching `reading/` note appears, adds `read_at`) | `rejected` (adds `rejected_at`; fed to S2 as negative seed).

Buffer is a queue, not a one-shot list — missing a day doesn't lose papers; old entries stay until acted on. Display sort: year desc, first-seen asc.

## Implementation — agent invokes on user's behalf

```bash
python3 .agent/skills/recommend_paper/scripts/recommend_papers.py [flags]
```

| Flag | Default | Effect |
|---|---|---|
| `--show N` | 5 | S2 entries printed to stdout |
| `--trending N` | 3 | HF entries printed to stdout; `0` disables |
| `--no-fetch` | off | Skip API calls; print from existing queue |
| `--reject ID ...` | — | Mark IDs rejected and exit |

Output is markdown to stdout. The agent reads it, summarizes for chat. State is the durable record; chat is the surface.

[^s2_recs]: <https://api.semanticscholar.org/api-docs/recommendations>
[^hf_daily]: <https://huggingface.co/api/daily_papers>
