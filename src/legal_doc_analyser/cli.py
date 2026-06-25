"""
Command-line interface.

Two subcommands:

    legal-doc-analyser analyse --file contract.pdf
    legal-doc-analyser analyse --text "This Agreement..." --format markdown
    cat contract.txt | legal-doc-analyser analyse
    legal-doc-analyser batch ./contracts --out ./analysis

This is a prototype. It performs information extraction and flags points for
human review; it does not give legal advice.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import report
from .batch import analyse_directory
from .extract import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    ExtractionError,
    analyse_text,
)
from .loaders import DocumentLoadError, load_from_path, load_from_stdin


def _read_single_document(args: argparse.Namespace) -> str:
    if args.file:
        return load_from_path(Path(args.file))
    if args.text:
        return args.text
    if not sys.stdin.isatty():
        return load_from_stdin()
    raise DocumentLoadError("No document provided. Use --file, --text, or pipe text via stdin.")


def _cmd_analyse(args: argparse.Namespace) -> int:
    try:
        document = _read_single_document(args)
        analysis = analyse_text(document, model=args.model, max_tokens=args.max_tokens)
    except DocumentLoadError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except ExtractionError as exc:
        print(f"Extraction failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # auth/API/etc. — report cleanly, no stack trace
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    source = Path(args.file).name if args.file else None
    if args.format == "markdown":
        rendered = report.to_markdown(analysis, source=source)
    else:
        rendered = json.dumps(analysis.model_dump(), indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(rendered)
    return 0


def _cmd_batch(args: argparse.Namespace) -> int:
    try:
        results = analyse_directory(
            Path(args.directory), Path(args.out), model=args.model, max_tokens=args.max_tokens
        )
    except (FileNotFoundError, DocumentLoadError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    ok = sum(1 for r in results if r.analysis is not None)
    failed = len(results) - ok
    print(f"Analysed {ok} document(s); {failed} failed. Outputs in {args.out}/", file=sys.stderr)
    return 0 if failed == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="legal-doc-analyser",
        description="Structured analysis of legal documents (prototype; not legal advice).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--model", default=DEFAULT_MODEL, help=f"Model to use (default: {DEFAULT_MODEL}).")
    common.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS, help="Maximum response tokens.")

    p_analyse = sub.add_parser("analyse", parents=[common], help="Analyse a single document.")
    src = p_analyse.add_mutually_exclusive_group()
    src.add_argument("--file", help="Path to a document (.txt, .md, .pdf, .docx).")
    src.add_argument("--text", help="Document text passed directly on the command line.")
    p_analyse.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format.")
    p_analyse.add_argument("--output", help="Write output to this file instead of stdout.")
    p_analyse.set_defaults(func=_cmd_analyse)

    p_batch = sub.add_parser("batch", parents=[common], help="Analyse every supported document in a folder.")
    p_batch.add_argument("directory", help="Folder containing documents to analyse.")
    p_batch.add_argument("--out", default="analysis", help="Output folder (default: ./analysis).")
    p_batch.set_defaults(func=_cmd_batch)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
