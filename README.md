# legal-doc-analyser

Turn an unstructured legal document — a contract, notice or policy, as **PDF, Word or text** — into **validated, structured data** and a set of **neutral flags for human review**. It extracts and flags; it does not advise.

> **Proof-of-concept, built through AI-assisted development.** A working prototype that shows how a legal professional can combine domain knowledge with foundational programming and an LLM to make unstructured legal text usable as data. It is **not** a production system and it does **not** give legal advice. Every output requires review by a qualified person.

---

## The problem it addresses

A great deal of early legal work is reading documents to find the same handful of things — who the parties are, the key dates and deadlines, who must do what, which clauses are present, and what looks unusual or incomplete. Doing this by hand over a stack of documents is slow and inconsistent.

This tool produces a **consistent, structured first pass**: the same fields, in the same shape, every time, as machine-readable JSON — plus a readable review report that points a human to the things worth checking. It is built to *assist* a reviewer, not to replace one.

## What it does — and does not do

**Does**
- Reads `.pdf`, `.docx`, `.txt` and `.md` (and text piped via stdin).
- Extracts a fixed schema: document type, summary, parties, effective date, governing law, key dates, obligations, notable clauses, and points for human review.
- **Shows its evidence** — for key findings it returns the short span of the document that supports them, so a human can verify rather than trust.
- Validates every result against a typed schema before returning it.
- Runs over a whole **folder** of documents, producing per-file JSON, a combined review report, and a CSV summary.

**Does not**
- It does **not** give legal advice, reach legal conclusions, or make recommendations.
- The “points for human review” are **neutral flags**, not advice — things a qualified person may wish to check.
- Output is only as reliable as the underlying model; **every result needs human review**.

## How it works

The design keeps four concerns separate and honest:

1. **Load** (`loaders.py`) — extract text from PDF/Word/text. Image-only (scanned) PDFs are detected and reported rather than silently mis-read; OCR is out of scope for this prototype.
2. **Extract** (`extract.py`) — the document is sent to the Anthropic API, which is **forced to call a single tool** whose input schema is generated from the data model. This guarantees structured output across models without relying on the model to format JSON correctly by itself.
3. **Validate** (`schema.py`) — the returned data is validated with **Pydantic** before it reaches you. This is what makes “validated” literal rather than aspirational.
4. **Report** (`report.py`) — the same validated result is rendered as machine-readable JSON, a human-readable Markdown review report, or a flat CSV summary row.

The boundary — *extract and flag, never advise* — is enforced in the schema field definitions and the system prompt, not bolted on as a disclaimer.

## Install

```bash
git clone https://github.com/MahmoudHusseinLawTech/legal-doc-analyser.git
cd legal-doc-analyser
pip install -e .                      # installs the `legal-doc-analyser` command
export ANTHROPIC_API_KEY="your-key"   # never hard-code or commit your key
```

Requires Python 3.10+ and an Anthropic API key.

## Usage

**Single document**
```bash
legal-doc-analyser analyse --file examples/sample_services_agreement.pdf
legal-doc-analyser analyse --file examples/sample_employment_offer.docx --format markdown
legal-doc-analyser analyse --text "This Agreement is made on..."
cat contract.txt | legal-doc-analyser analyse
```

**A folder of documents (batch)**
```bash
legal-doc-analyser batch examples --out analysis
# writes analysis/<name>.json per document, plus analysis/report.md and analysis/summary.csv
```

Options: `--format json|markdown`, `--output FILE`, `--model`, `--max-tokens`.

## Example output

*Illustrative — the analysis content below is fictional; the structure and formatting are the tool's actual output.*

```json
{
  "document_type": "Mutual Non-Disclosure Agreement",
  "summary": "An NDA between Meridian Labs Ltd and Northwind Analytics Ltd for a potential data-analytics collaboration.",
  "parties": ["Meridian Labs Ltd (Discloser)", "Northwind Analytics Ltd (Recipient)"],
  "effective_date": "1 March 2026",
  "governing_law": "England and Wales",
  "obligations": [
    {
      "party": "Northwind Analytics Ltd",
      "obligation": "Keep Confidential Information secret and not disclose it to third parties",
      "source_text": "The Recipient shall keep all Confidential Information secret"
    }
  ],
  "notable_clauses": ["Confidentiality", "Return of materials", "Governing law"],
  "review_points": [
    {
      "point": "The three-year confidentiality period has no stated start point",
      "category": "date_or_deadline_gap",
      "source_text": "shall continue for a period of three (3) years"
    }
  ],
  "extraction_confidence": "high"
}
```

## Demo

*Placeholder — add a terminal screenshot or asciinema recording here (`docs/demo.gif`).*

## Project structure

```
src/legal_doc_analyser/
  schema.py     typed data model (Pydantic) + the tool spec derived from it
  loaders.py    pdf / docx / txt / stdin -> text
  extract.py    forced tool-use call -> validated DocumentAnalysis
  report.py     analysis -> Markdown report / CSV row
  batch.py      folder -> per-file JSON + combined report + CSV
  cli.py        `analyse` and `batch` commands
tests/          unit tests (run without an API key)
examples/       fictional sample documents (.txt, .docx, .pdf)
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

The suite runs **without an API key**: loaders are tested against the sample files, and the extraction pipeline is tested with a mock client that mimics the API response shape.

## Roadmap (not yet built)

Clearly marked as future work, not present capability:
- Document **comparison** (a draft against a template or standard form).
- **Document-type-aware** schemas (an NDA, a lease and an employment contract have different salient fields).
- **OCR** for scanned/image-only PDFs.
- Native **structured-outputs** mode (`output_format`) as an alternative to forced tool use.

## Boundaries and responsible use

*Proof-of-concept for demonstration and research only. Not legal advice; creates no lawyer–client relationship; outputs require review by a qualified person before any reliance. Built through AI-assisted development. Use only documents you are entitled to process, and do not submit confidential or personal data to a third-party API without an appropriate basis.*

## Licence

MIT — see [LICENSE](LICENSE).

## About

Built by **Mahmoud Hussein**, an Egypt-qualified lawyer (registered at Appeal level), through AI-assisted development — directing and assembling AI-generated code on a foundation of Python, with the legal design and review his own.

