from legal_doc_analyser.schema import (
    TOOL_NAME,
    DocumentAnalysis,
    build_tool,
)

GOOD = {
    "document_type": "Mutual Non-Disclosure Agreement",
    "summary": "An NDA between two companies.",
    "parties": ["Meridian Labs Ltd", "Northwind Analytics Ltd"],
    "effective_date": "1 March 2026",
    "governing_law": "England and Wales",
    "key_dates": [{"date": "1 March 2026", "description": "Agreement date"}],
    "obligations": [
        {"party": "Northwind Analytics Ltd", "obligation": "Keep information confidential"}
    ],
    "notable_clauses": ["Confidentiality", "Governing law"],
    "review_points": [
        {
            "point": "No defined start point for the three-year period",
            "category": "date_or_deadline_gap",
        }
    ],
    "extraction_confidence": "high",
}


def test_validates_a_good_payload():
    analysis = DocumentAnalysis.model_validate(GOOD)
    assert analysis.document_type == "Mutual Non-Disclosure Agreement"
    assert analysis.obligations[0].party == "Northwind Analytics Ltd"
    assert analysis.extraction_confidence.value == "high"
    # optional evidence field defaults to None when absent
    assert analysis.key_dates[0].source_text is None


def test_round_trips_through_dump():
    analysis = DocumentAnalysis.model_validate(GOOD)
    again = DocumentAnalysis.model_validate(analysis.model_dump())
    assert again == analysis


def test_tool_spec_matches_schema():
    tool = build_tool()
    assert tool["name"] == TOOL_NAME
    schema = tool["input_schema"]
    assert schema["type"] == "object"
    assert "document_type" in schema["properties"]
    assert "review_points" in schema["properties"]
