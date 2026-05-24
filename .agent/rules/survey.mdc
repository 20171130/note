---
description: Finding information and writing it down: sourcing, citations, literature review.
alwaysApply: false
---

# Academic Writing
- Write findings into a note with inline references `[text](url)` at point of use.
- Notes (including logs) are readable prose, not append-only transcripts. Keep only what reflects current understanding; remove outdated or redundant content once resolved. Prefer brief conclusions with citations over raw technical detail.
- Citations: external sources go in footnotes (with optional short note); intra-repo references are inline, e.g. `[AGENTS](AGENTS.md#academic-writing)`.

# Literature Review
When surveying a topic, create `/knowledge/survey_{topic}.md` organized as:

```markdown
# Summary
First, describe the central topic.
Describe milestone breakthroughs and paradigm shifts, trends and current focus of work.
Distinguish established best practice (or competing popular paradigms), emerging practice (solid results, not yet widely adopted), and questionable one-offs (weak results, or strong claims with no follow-up years after publication).

# Read List
## {Year}
### label, e.g. `attention_is_all_you_need_2017`
Title
Summary (may contain references)
Outbound links: important keywords and citations.

# To Read List
keywords and citations
```

## Crawl
Loop: pick the top To-Read entry, download to `note/tmp/<label>.{pdf,html}`, read it, add a Read-List entry, then refresh To-Read from its citations and keywords. Update the Summary every 3–5 papers and check in with the user.

> Extract PDF text with `pypdf`; fall back to ar5iv (`https://ar5iv.labs.arxiv.org/html/<id>`) only when the PDF is scanned or layout matters.

## Read
When the user drafts his own summary for an entry, read the paper yourself, [review](writing#review) the user's summary and interact to resolve questions, then [fix](writing#fix), [optimize](writing#optimize), and finally [normalize](writing#normalize) by moving the body to `reading/<year>/<label>.md`.
