from pathlib import Path

import pytest

from legal_doc_analyser.loaders import (
    DocumentLoadError,
    find_documents,
    load_from_path,
)

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_loads_txt():
    text = load_from_path(EXAMPLES / "sample_nda.txt")
    assert "Meridian Labs Ltd" in text


def test_loads_docx_including_table_cells():
    text = load_from_path(EXAMPLES / "sample_employment_offer.docx")
    # 'Operations Coordinator' lives in a table cell, so this proves table extraction.
    assert "Operations Coordinator" in text
    assert "Harbour Logistics Ltd" in text


def test_loads_pdf():
    text = load_from_path(EXAMPLES / "sample_services_agreement.pdf")
    assert "Coastal Software Ltd" in text


def test_unsupported_extension_raises():
    with pytest.raises(DocumentLoadError):
        load_from_path(EXAMPLES / "nonexistent.xyz")


def test_missing_file_raises():
    with pytest.raises(DocumentLoadError):
        load_from_path(EXAMPLES / "does_not_exist.txt")


def test_find_documents_lists_supported_files():
    found = {p.name for p in find_documents(EXAMPLES)}
    assert {
        "sample_nda.txt",
        "sample_employment_offer.docx",
        "sample_services_agreement.pdf",
    } <= found
