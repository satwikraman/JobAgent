"""
Data models for the Job Application Agent
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from pathlib import Path


class ApplicationStatus(str, Enum):
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    APPLIED     = "applied"
    DRY_RUN     = "dry_run"
    FAILED      = "failed"
    SKIPPED     = "skipped"
    INTERVIEW   = "interview"   # manually updated
    REJECTED    = "rejected"    # manually updated
    OFFER       = "offer"       # manually updated


@dataclass
class Resume:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""
    summary: str = ""
    skills: list = field(default_factory=list)
    experience: list = field(default_factory=list)   # [{title, company, duration, bullets}]
    education: str = ""
    raw_text: str = ""
    file_path: Optional[Path] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "linkedin": self.linkedin,
            "github": self.github,
            "website": self.website,
            "summary": self.summary,
            "skills": self.skills,
            "experience": self.experience,
            "education": self.education,
        }


@dataclass
class Job:
    title: str = ""
    company: str = ""
    location: str = ""
    url: str = ""
    description: str = ""
    salary: str = ""
    job_type: str = ""          # full-time, part-time, contract
    source: str = ""            # indeed, linkedin, etc.
    posted_date: str = ""
    match_score: int = 0
    match_reasons: list = field(default_factory=list)
    easy_apply: bool = False    # one-click apply available
    raw_html: str = ""


@dataclass
class ApplicationResult:
    success: bool = False
    error: str = ""
    screenshot_path: Optional[str] = None
    confirmation_text: str = ""


@dataclass
class Application:
    job: Optional[Job] = None
    resume: Optional[Resume] = None
    status: ApplicationStatus = ApplicationStatus.PENDING
    applied_at: str = ""
    error: str = ""
    cover_letter: str = ""
    notes: str = ""
    screenshot_path: str = ""
    confirmation_text: str = ""
