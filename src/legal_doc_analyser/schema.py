"""
Data model for a single legal-document analysis.

The schema is deliberately an *information-extraction* shape. It records what a
document says and flags points a human may wish to check. It carries no legal
advice, no legal conclusions and no recommendations. The ``review_points`` field
is a list of neutral flags for a human reviewer, not a list of recommendations.

Because the model is defined with Pydantic, every result returned by the tool is
validated against this schema before it reaches the user: the word "validated" in
the README is literal, not aspirational.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """How confident the model is in the *extraction* — not a legal assessment."""

    low = "low"
    medium = "medium"
    high = "high"


class ReviewCategory(str, Enum):
    """The nature of a review flag. Describes *what kind* of thing to check,
    never *how risky* it is — a risk rating would read as a legal judgement."""

    missing_information = "missing_information"
    ambiguity = "ambiguity"
    unusual_term = "unusual_term"
    internal_inconsistency = "internal_inconsistency"
    date_or_deadline_gap = "date_or_deadline_gap"
    other = "other"


class KeyDate(BaseModel):
    date: str = Field(description="The date exactly as written in the document.")
    description: str = Field(description="What this date refers to (e.g. 'commencement', 'notice deadline').")
    source_text: Optional[str] = Field(
        default=None,
        description="The short span of the document that supports this date, quoted so a human can verify it.",
    )


class Obligation(BaseModel):
    party: str = Field(description="The party who bears the obligation.")
    obligation: str = Field(description="A plain-English statement of what that party must do.")
    source_text: Optional[str] = Field(
        default=None,
        description="The short span of the document that supports this obligation, quoted so a human can verify it.",
    )


class ReviewPoint(BaseModel):
    """A neutral flag for a human reviewer. This is NOT legal advice and NOT a
    recommendation; it is a prompt for a qualified person to look at something."""

    point: str = Field(description="A neutral factual flag for a human to check. Not advice, not a recommendation.")
    category: ReviewCategory = Field(description="The kind of flag this is.")
    source_text: Optional[str] = Field(
        default=None,
        description="The span of the document the flag relates to, where applicable, quoted for verification.",
    )


class DocumentAnalysis(BaseModel):
    """Structured, machine-readable analysis of a single legal document.

    An information-extraction result only: it states what the document says and
    flags points for human review. It contains no legal advice or conclusions.
    """

    document_type: str = Field(description="Best description of the document type, e.g. 'Mutual Non-Disclosure Agreement'.")
    summary: str = Field(description="One or two plain-English sentences describing the document.")
    parties: list[str] = Field(default_factory=list, description="Each named party or role in the document.")
    effective_date: Optional[str] = Field(default=None, description="The effective / commencement date, or null if not stated.")
    governing_law: Optional[str] = Field(default=None, description="The stated governing law or jurisdiction, or null if not stated.")
    key_dates: list[KeyDate] = Field(default_factory=list, description="Dates and deadlines found in the document.")
    obligations: list[Obligation] = Field(default_factory=list, description="Who must do what, per the document.")
    notable_clauses: list[str] = Field(
        default_factory=list,
        description="Types of clause present, e.g. termination, liability, confidentiality, governing law, indemnity.",
    )
    review_points: list[ReviewPoint] = Field(
        default_factory=list,
        description="Neutral flags for a human reviewer to check. NOT advice and NOT recommendations.",
    )
    extraction_confidence: ConfidenceLevel = Field(
        description="The model's confidence in the quality of this extraction (not a legal assessment).",
    )


# --- Tool specification derived from the schema above -----------------------

TOOL_NAME = "record_document_analysis"


def build_tool() -> dict:
    """Return the Anthropic tool definition for forced structured extraction.

    The JSON schema is generated directly from :class:`DocumentAnalysis`, so the
    tool and the validated Python model can never drift apart.
    """

    return {
        "name": TOOL_NAME,
        "description": (
            "Record the structured, extraction-only analysis of the legal document. "
            "Call this exactly once with your findings. Do not give legal advice, "
            "reach legal conclusions or make recommendations."
        ),
        "input_schema": DocumentAnalysis.model_json_schema(),
    }
