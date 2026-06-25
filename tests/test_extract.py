"""
Exercise the extraction pipeline without network access or an API key by
injecting a fake client that mimics the Anthropic response shape (a list of
content blocks, one of which is a ``tool_use`` block carrying ``input``).
"""

from types import SimpleNamespace

import pytest

from legal_doc_analyser.extract import ExtractionError, analyse_text
from legal_doc_analyser.schema import TOOL_NAME

VALID_TOOL_INPUT = {
    "document_type": "Mutual Non-Disclosure Agreement",
    "summary": "An NDA between two companies.",
    "parties": ["Meridian Labs Ltd", "Northwind Analytics Ltd"],
    "effective_date": "1 March 2026",
    "governing_law": "England and Wales",
    "key_dates": [],
    "obligations": [
        {"party": "Northwind Analytics Ltd", "obligation": "Keep information confidential"}
    ],
    "notable_clauses": ["Confidentiality"],
    "review_points": [],
    "extraction_confidence": "high",
}


class _FakeMessages:
    def __init__(self, message):
        self._message = message
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._message


class FakeClient:
    """Minimal stand-in for anthropic.Anthropic()."""

    def __init__(self, content_blocks):
        message = SimpleNamespace(content=content_blocks)
        self.messages = _FakeMessages(message)


def _tool_use_block(name, payload):
    return SimpleNamespace(type="tool_use", name=name, input=payload)


def test_analyse_text_returns_validated_model():
    client = FakeClient([_tool_use_block(TOOL_NAME, VALID_TOOL_INPUT)])
    result = analyse_text("Some document text", client=client)
    assert result.document_type == "Mutual Non-Disclosure Agreement"
    assert result.obligations[0].party == "Northwind Analytics Ltd"
    # and the call forced our tool
    sent = client.messages.calls[0]
    assert sent["tool_choice"] == {"type": "tool", "name": TOOL_NAME}


def test_missing_tool_call_raises():
    text_block = SimpleNamespace(type="text", text="I cannot do that.")
    client = FakeClient([text_block])
    with pytest.raises(ExtractionError):
        analyse_text("Some document text", client=client)


def test_empty_document_raises():
    client = FakeClient([_tool_use_block(TOOL_NAME, VALID_TOOL_INPUT)])
    with pytest.raises(ExtractionError):
        analyse_text("   ", client=client)
