"""
Batch analysis: run the analyser over every supported document in a folder.

This mirrors real first-pass review work (a stack of NDAs, a folder of supplier
contracts). For each document it writes a per-file JSON analysis; across the set
it writes a combined Markdown report and a CSV summary so a reviewer can triage
at a glance and then drill into the structured data.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from . import report
from .extract import DEFAULT_MAX_TOKENS, DEFAULT_MODEL, analyse_text
from .loaders import find_documents, load_from_path
from .schema import DocumentAnalysis


@dataclass
class BatchResult:
    source: str
    analysis: Optional[DocumentAnalysis] = None
    error: Optional[str] = None


def analyse_directory(
    directory: Path,
    output_dir: Path,
    *,
    client: Optional[Any] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> list[BatchResult]:
    """Analyse every supported document in ``directory``; write outputs to ``output_dir``.

    Returns one :class:`BatchResult` per document. A failure on one document does
    not stop the batch — its error is recorded and the run continues.
    """
    documents = find_documents(directory)
    if not documents:
        raise FileNotFoundError(f"No supported documents found in {directory}.")

    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[BatchResult] = []

    for path in documents:
        print(f"Analysing {path.name} ...", file=sys.stderr)
        try:
            text = load_from_path(path)
            analysis = analyse_text(text, client=client, model=model, max_tokens=max_tokens)
            results.append(BatchResult(source=path.name, analysis=analysis))
            (output_dir / f"{path.stem}.json").write_text(
                json.dumps(analysis.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as exc:  # keep going; one bad file shouldn't sink the batch
            print(f"  ! failed: {exc}", file=sys.stderr)
            results.append(BatchResult(source=path.name, error=str(exc)))

    _write_combined_outputs(results, output_dir)
    return results


def _write_combined_outputs(results: list[BatchResult], output_dir: Path) -> None:
    md_parts: list[str] = ["# Batch review report", ""]
    rows: list[dict[str, str]] = []

    for result in results:
        if result.analysis is not None:
            md_parts.append(report.to_markdown(result.analysis, source=result.source))
            md_parts.append("\n---\n")
            rows.append(report.to_csv_row(result.analysis, source=result.source))
        else:
            md_parts.append(f"## {result.source}\n\n*Could not analyse: {result.error}*\n\n---\n")

    (output_dir / "report.md").write_text("\n".join(md_parts), encoding="utf-8")
    if rows:
        (output_dir / "summary.csv").write_text(report.rows_to_csv(rows), encoding="utf-8")
