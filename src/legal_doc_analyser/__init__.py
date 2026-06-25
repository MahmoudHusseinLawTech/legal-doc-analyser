"""
legal-doc-analyser — structured, machine-readable analysis of legal documents.

A proof-of-concept that combines legal domain knowledge with foundational
programming and an LLM to turn an unstructured legal document into validated,
structured data and a set of neutral flags for human review. It extracts and
flags only; it does not give legal advice.

Public API
----------
    from legal_doc_analyser import analyse_text, DocumentAnalysis
"""

from __future__ import annotations

from .extract import ExtractionError, analyse_text
from .loaders import DocumentLoadError, load_from_path
from .schema import DocumentAnalysis

__version__ = "0.2.0"

__all__ = [
    "analyse_text",
    "DocumentAnalysis",
    "DocumentLoadError",
    "ExtractionError",
    "__version__",
]
