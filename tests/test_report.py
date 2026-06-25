from legal_doc_analyser import report
from legal_doc_analyser.schema import DocumentAnalysis

ANALYSIS = DocumentAnalysis.model_validate(
    {
        "document_type": "Services Agreement",
        "summary": "A software support agreement.",
        "parties": ["Coastal Software Ltd", "Brightwater Retail Ltd"],
        "effective_date": "5 February 2026",
        "governing_law": "England and Wales",
        "key_dates": [
            {"date": "5 February 2026", "description": "Commencement", "source_text": "commences on 5 February 2026"}
        ],
        "obligations": [
            {"party": "Client", "obligation": "Pay GBP 4,000 per month", "source_text": "GBP 4,000 per month"}
        ],
        "notable_clauses": ["Fees", "Termination", "Liability"],
        "review_points": [
            {"point": "Auto-renewal with no stated notice period", "category": "unusual_term"}
        ],
        "extraction_confidence": "medium",
    }
)


def test_markdown_has_sections_and_boundary():
    md = report.to_markdown(ANALYSIS, source="sample.pdf")
    assert "# Document Analysis — sample.pdf" in md
    assert "## Obligations" in md
    assert "## Points for human review" in md
    assert "Coastal Software Ltd" in md
    # the supporting evidence is rendered as a quote
    assert "> GBP 4,000 per month" in md
    # the not-advice boundary must always be present
    assert "not legal advice" in md.lower()


def test_csv_row_counts_and_fields():
    row = report.to_csv_row(ANALYSIS, source="sample.pdf")
    assert row["source"] == "sample.pdf"
    assert row["obligations"] == "1"
    assert row["review_points"] == "1"
    assert row["extraction_confidence"] == "medium"


def test_rows_to_csv_has_header():
    csv_text = report.rows_to_csv([report.to_csv_row(ANALYSIS, source="sample.pdf")])
    assert csv_text.splitlines()[0] == ",".join(report.CSV_FIELDS)
