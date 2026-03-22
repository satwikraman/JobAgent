"""
Resume Parser - Extracts structured data from PDF and DOCX resumes using Claude AI
"""

import json
from pathlib import Path
from models import Resume
from claude_client import ClaudeClient


class ResumeParser:
    """
    Parses a resume file (PDF or DOCX) and extracts structured data
    using Claude for intelligent extraction.
    """

    def __init__(self, claude: ClaudeClient):
        self.claude = claude

    def parse(self, path: Path) -> Resume:
        """Main entry point — detects file type and parses accordingly."""
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            raw_text = self._extract_pdf_text(path)
        elif suffix in (".docx", ".doc"):
            raw_text = self._extract_docx_text(path)
        elif suffix == ".txt":
            raw_text = path.read_text(encoding="utf-8")
        else:
            raise ValueError(f"Unsupported resume format: {suffix}. Use PDF, DOCX, or TXT.")

        return self._extract_with_claude(raw_text, path)

    # ─────────────────────────────────────────────
    # TEXT EXTRACTION
    # ─────────────────────────────────────────────

    def _extract_pdf_text(self, path: Path) -> str:
        """Extract text from PDF using pdfminer."""
        try:
            from pdfminer.high_level import extract_text
            return extract_text(str(path))
        except ImportError:
            raise ImportError("pdfminer.six is required: pip install pdfminer.six")

    def _extract_docx_text(self, path: Path) -> str:
        """Extract text from DOCX using python-docx."""
        try:
            from docx import Document
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except ImportError:
            raise ImportError("python-docx is required: pip install python-docx")

    # ─────────────────────────────────────────────
    # AI EXTRACTION
    # ─────────────────────────────────────────────

    def _extract_with_claude(self, raw_text: str, path: Path) -> Resume:
        """Use Claude to extract structured fields from raw resume text."""
        prompt = f"""
Extract structured data from this resume. Return a JSON object with these exact keys:
- name (string)
- email (string)
- phone (string)
- location (string, city/state)
- linkedin (string URL or empty)
- github (string URL or empty)
- website (string URL or empty)
- summary (string, professional summary or objective, max 3 sentences)
- skills (array of strings, list every technical skill, tool, language, framework)
- experience (array of objects with keys: title, company, duration, bullets)
  - bullets: array of strings (up to 4 key accomplishments per role)
- education (string, formatted as "Degree, Major — University, Year")

RESUME TEXT:
{raw_text[:6000]}

Return only valid JSON, no markdown fences, no explanation.
"""
        data = self.claude.extract_json(prompt, max_tokens=2000)

        resume = Resume(
            name=data.get("name", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            location=data.get("location", ""),
            linkedin=data.get("linkedin", ""),
            github=data.get("github", ""),
            website=data.get("website", ""),
            summary=data.get("summary", ""),
            skills=data.get("skills", []),
            experience=data.get("experience", []),
            education=data.get("education", ""),
            raw_text=raw_text,
            file_path=path
        )

        return resume
