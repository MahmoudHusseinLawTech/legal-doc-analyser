"""
Render a validated :class:`DocumentAnalysis` into human-readable outputs.

The same structured result drives two renderings: a Markdown *review report* a
person can read, and a flat CSV summary row for a batch overview. Every report
carries a footer making the boundary explicit — extraction and flags only, not
legal advice.
"""

from __future__ import annotations

import csv
import io

from .schema import DocumentAnalysis

BOUNDARY_FOOTER = (
    "_This is an automated, information-extraction result and a set of neutral flags "
    "for human review. It is not legal advice, reaches no legal conclusions, and must "
    "be reviewed by a qualified person before any reliance._"
)

# Column order for CSV / batch summaries.
CSV_FIELDS = [
    "source",
    "document_type",
    "parties",
    "effective_date",
    "governing_law",
    "obligations",
    "review_points",
    "extraction_confidence",
]


def _or_dash(value: object) -> str:
    return str(value) if value not in (None, "", []) else "—"


def to_markdown(analysis: DocumentAnalysis, *, source: str | None = None) -> str:
    """Render the analysis as a Markdown review report."""
    lines: list[str] = []
    title = f"Document Analysis — {source}" if source else "Document Analysis"
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Document type:** {_or_dash(analysis.document_type)}  ")
    lines.append(f"**Summary:** {_or_dash(analysis.summary)}  ")
    lines.append(f"**Effective date:** {_or_dash(analysis.effective_date)}  ")
    lines.append(f"**Governing law:** {_or_dash(analysis.governing_law)}  ")
    lines.append(f"**Extraction confidence:** {analysis.extraction_confidence.value}")
    lines.append("")

    lines.append("## Parties")
    if analysis.parties:
        lines.extend(f"- {p}" for p in analysis.parties)
    else:
        lines.append("- —")
    lines.append("")

    lines.append("## Key dates")
    if analysis.key_dates:
        for d in analysis.key_dates:
            lines.append(f"- **{d.date}** — {d.description}")
            if d.source_text:
                lines.append(f"  > {d.source_text}")
    else:
        lines.append("- —")
    lines.append("")

    lines.append("## Obligations")
    if analysis.obligations:
        for o in analysis.obligations:
            lines.append(f"- **{o.party}:** {o.obligation}")
            if o.source_text:
                lines.append(f"  > {o.source_text}")
    else:
        lines.append("- —")
    lines.append("")

    lines.append("## Notable clauses")
    if analysis.notable_clauses:
        lines.extend(f"- {c}" for c in analysis.notable_clauses)
    else:
        lines.append("- —")
    lines.append("")

    lines.append("## Points for human review")
    lines.append("_Neutral flags only — not advice._")
    lines.append("")
    if analysis.review_points:
        for r in analysis.review_points:
            label = r.category.value.replace("_", " ")
            lines.append(f"- _({label})_ {r.point}")
            if r.source_text:
                lines.append(f"  > {r.source_text}")
    else:
        lines.append("- —")
    lines.append("")

    lines.append("---")
    lines.append(BOUNDARY_FOOTER)
    return "\n".join(lines) + "\n"


def to_csv_row(analysis: DocumentAnalysis, *, source: str) -> dict[str, str]:
    """Flatten the analysis into a single CSV-friendly row."""
    return {
        "source": source,
        "document_type": analysis.document_type,
        "parties": "; ".join(analysis.parties),
        "effective_date": analysis.effective_date or "",
        "governing_law": analysis.governing_law or "",
        "obligations": str(len(analysis.obligations)),
        "review_points": str(len(analysis.review_points)),
        "extraction_confidence": analysis.extraction_confidence.value,
    }


def rows_to_csv(rows: list[dict[str, str]]) -> str:
    """Render a list of summary rows as CSV text."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()
