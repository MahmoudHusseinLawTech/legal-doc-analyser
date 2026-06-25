"""
Send a document to the model and return a *validated* structured analysis.

The structure is guaranteed two ways: the model is forced to call a single tool
whose input schema is generated from the Pydantic model (``tool_choice`` of type
``tool``), and the returned input is then validated with Pydantic before it is
handed back. The model is instructed to extract and flag only — never to advise.
"""

from __future__ import annotations

import sys
from typing import Any, Optional

from .schema import TOOL_NAME, DocumentAnalysis, build_tool

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 4096

# A generous soft cap. Beyond this we warn (never silently truncate — dropping
# text from a legal document would be worse than a clear warning).
SOFT_CHAR_LIMIT = 200_000

SYSTEM_PROMPT = """You are an information-extraction assistant for legal documents.

You do NOT give legal advice, you do NOT reach legal conclusions, and you do NOT
make recommendations. You extract, organise and summarise what the document says,
and you flag points a human reviewer may wish to check.

Base every field strictly on the text provided; never invent facts. Where the
schema asks for a supporting 'source_text', quote the shortest span of the
document that supports the finding, so a human can verify it. If information is
not present, use null or an empty list.

The 'review_points' you record are neutral flags for a human to check — missing
information, ambiguity, unusual terms, internal inconsistencies, date or deadline
gaps. They are NOT advice and NOT recommendations.

Return your analysis by calling the provided tool exactly once."""

USER_TEMPLATE = (
    "Analyse the following legal document and record your findings by calling the tool.\n\n"
    "--- DOCUMENT START ---\n{document}\n--- DOCUMENT END ---"
)


class ExtractionError(Exception):
    """Raised when the model does not return a usable structured analysis."""


def _first_tool_input(message: Any, tool_name: str) -> dict:
    """Pull the input of the first matching tool_use block out of a response."""
    for block in getattr(message, "content", []):
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == tool_name:
            return block.input
    raise ExtractionError("The model did not return the expected structured tool call.")


def analyse_text(
    document_text: str,
    *,
    client: Optional[Any] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> DocumentAnalysis:
    """Analyse document text and return a validated :class:`DocumentAnalysis`.

    Args:
        document_text: The raw text of the document.
        client: An Anthropic client. If omitted, a default client is created,
            which reads ``ANTHROPIC_API_KEY`` from the environment. Injecting a
            client makes this function testable without network access.
        model: The model to use.
        max_tokens: Maximum response tokens.
    """
    if not document_text or not document_text.strip():
        raise ExtractionError("The document is empty.")

    if len(document_text) > SOFT_CHAR_LIMIT:
        print(
            f"Warning: document is large ({len(document_text):,} characters). "
            "It may exceed the model's context window or increase cost.",
            file=sys.stderr,
        )

    if client is None:
        import anthropic

        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        tools=[build_tool()],
        tool_choice={"type": "tool", "name": TOOL_NAME},
        messages=[{"role": "user", "content": USER_TEMPLATE.format(document=document_text)}],
    )

    tool_input = _first_tool_input(message, TOOL_NAME)
    # Pydantic validation: this is what makes the output 'validated'.
    return DocumentAnalysis.model_validate(tool_input)
