"""
Gemini API Client - Direct API calls to Google AI
"""

import requests
from typing import Optional


class GeminiClient:
    """
    Direct API calls to Google AI Gemini API.
    Used by all agent components that need AI reasoning.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def complete(self, prompt: str, max_tokens: int = 1000, system: str = "") -> str:
        """Simple text completion — returns the assistant's text response."""
        if system:
            prompt = f"{system}\n\n{prompt}"

        url = f"{self.base_url}/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens
            }
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                print(f"Gemini API error: Model or endpoint not found. Please ensure you have a valid Gemini API key from Google AI Studio.")
                print(f"Get your key at: https://aistudio.google.com/app/apikey")
            else:
                print(f"Gemini API error: {e}")
            return ""
        except Exception as e:
            print(f"Gemini API error: {e}")
            return ""

    def extract_json(self, prompt: str, max_tokens: int = 1000) -> dict:
        """
        Ask Gemini to respond with JSON only.
        Returns parsed dict, or empty dict on failure.
        """
        import json
        system = (
            "You are a data extraction assistant. "
            "Always respond with valid JSON only — no markdown, no explanation, no backticks."
        )
        try:
            text = self.complete(prompt, max_tokens=max_tokens, system=system)
            # Strip any accidental markdown fences
            text = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(text)
        except Exception:
            return {}

    def generate_cover_letter(self, resume_dict: dict, job: dict) -> str:
        """Generate a tailored cover letter."""
        prompt = f"""
Write a concise, professional cover letter for this job application.
Keep it under 250 words. Use a confident, natural tone. Do NOT use generic filler phrases.
Focus on 2-3 specific, concrete reasons why this candidate fits this role.

CANDIDATE:
{resume_dict}

JOB:
Title: {job.get('title')}
Company: {job.get('company')}
Description: {job.get('description', '')[:1000]}

Write only the cover letter body (no date, no address block needed).
"""
        return self.complete(prompt, max_tokens=500)

    def answer_screening_question(self, question: str, resume_dict: dict, job: dict) -> str:
        """
        Generate a concise answer to a job application screening question.
        Used by the form filler for free-text fields.
        """
        prompt = f"""
Answer this job application question concisely and professionally (1-3 sentences max).
Base your answer on the candidate's background. Be specific, not generic.

QUESTION: {question}

CANDIDATE SUMMARY:
- Name: {resume_dict.get('name')}
- Skills: {', '.join(resume_dict.get('skills', [])[:15])}
- Most recent role: {resume_dict.get('experience', [{}])[0].get('title', 'N/A')} at {resume_dict.get('experience', [{}])[0].get('company', 'N/A')}

JOB: {job.get('title')} at {job.get('company')}

Respond with just the answer text.
"""
        return self.complete(prompt, max_tokens=150)

    def extract_json(self, prompt: str, max_tokens: int = 1000) -> dict:
        """
        Ask Gemini to respond with JSON only.
        Returns parsed dict, or empty dict on failure.
        """
        import json
        system = (
            "You are a data extraction assistant. "
            "Always respond with valid JSON only — no markdown, no explanation, no backticks."
        )
        try:
            text = self.complete(prompt, max_tokens=max_tokens, system=system)
            # Strip any accidental markdown fences
            text = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(text)
        except Exception:
            return {}

    def generate_cover_letter(self, resume_dict: dict, job: dict) -> str:
        """Generate a tailored cover letter."""
        prompt = f"""
Write a concise, professional cover letter for this job application.
Keep it under 250 words. Use a confident, natural tone. Do NOT use generic filler phrases.
Focus on 2-3 specific, concrete reasons why this candidate fits this role.

CANDIDATE:
{resume_dict}

JOB:
Title: {job.get('title')}
Company: {job.get('company')}
Description: {job.get('description', '')[:1000]}

Write only the cover letter body (no date, no address block needed).
"""
        return self.complete(prompt, max_tokens=500)

    def answer_screening_question(self, question: str, resume_dict: dict, job: dict) -> str:
        """
        Generate a concise answer to a job application screening question.
        Used by the form filler for free-text fields.
        """
        prompt = f"""
Answer this job application question concisely and professionally (1-3 sentences max).
Base your answer on the candidate's background. Be specific, not generic.

QUESTION: {question}

CANDIDATE SUMMARY:
- Name: {resume_dict.get('name')}
- Skills: {', '.join(resume_dict.get('skills', [])[:15])}
- Most recent role: {resume_dict.get('experience', [{}])[0].get('title', 'N/A')} at {resume_dict.get('experience', [{}])[0].get('company', 'N/A')}

JOB: {job.get('title')} at {job.get('company')}

Respond with just the answer text.
"""
        return self.complete(prompt, max_tokens=150)
