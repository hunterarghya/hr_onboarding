"""
PDF parsing tool — extract text from PDF using pypdf.

Converted from the user's PdfReader-based extractor.
"""

import os
from pypdf import PdfReader
from pypdf import PdfReader
from google.adk.tools import FunctionTool


def parse_pdf(filepath: str) -> dict:
    """Extract text content from a local PDF file.

    Args:
        filepath: Path to the PDF file saved by gmail_search.

    Returns:
        Dictionary with key 'text' containing the extracted text.
    """
    if not os.path.exists(filepath):
        return {"text": "", "page_count": 0, "has_content": False}

    with open(filepath, "rb") as f:
        reader = PdfReader(f)
        pages_text = []
        for page in reader.pages:
            try:
                pages_text.append(page.extract_text() or "")
            except Exception:
                pages_text.append("")

        full_text = "\n".join(pages_text).strip()
        # Truncate to ~400 tokens (1500 chars) to stay within tight 6000 TPM rate limits
        if len(full_text) > 1500:
            full_text = full_text[:1500] + "... [TRUNCATED]"

        return {
            "text": full_text,
            "page_count": len(reader.pages),
            "has_content": bool(full_text),
        }


# ── ADK FunctionTool wrapper ──────────────────────────────
parse_pdf_tool = FunctionTool(func=parse_pdf)
