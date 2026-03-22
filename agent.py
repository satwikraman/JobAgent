"""
Core Job Agent - Orchestrates resume parsing, job search, and applications
"""

import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

from resume_parser import ResumeParser
from job_searcher import JobSearcher
from form_filler import FormFiller
from models import Resume, Job, Application, ApplicationStatus
from config import Config
from database import Database
from claude_client import ClaudeClient

console = Console()

class JobAgent:
    """
    Main agent that coordinates all subsystems.
    Uses Claude as the AI brain for decision making.
    """

    def __init__(self, config_path: str = "config.yaml"):
        self.config = Config(config_path)
        self.db = Database()
        self.claude = ClaudeClient(api_key=self.config.get("anthropic_api_key"))
        self.resume_parser = ResumeParser(self.claude)
        self.job_searcher = JobSearcher(self.config)
        self.form_filler = FormFiller(self.config, self.claude)

        console.print(Panel.fit(
            "[bold cyan]🤖 Job Application Agent[/bold cyan]\n"
            "[dim]Powered by Claude AI[/dim]",
            border_style="cyan"
        ))

    # ─────────────────────────────────────────────
    # PUBLIC COMMANDS
    # ─────────────────────────────────────────────

    def search_jobs(
        self,
        resume_path: Path,
        role: str,
        location: str,
        limit: int = 20,
        min_score: int = 70
    ):
        """Search for jobs matching the resume and display results."""
        resume = self._load_resume(resume_path)
        
        # If no role specified, extract suitable roles from resume
        if not role:
            role = self._extract_suitable_roles(resume)
            if not role:
                console.print("[red]❌ Could not extract suitable roles from resume.[/red]")
                return
        
        jobs = self._find_matching_jobs(resume, role, location, limit, min_score)
        self._display_jobs_table(jobs)
        console.print(f"\n[green]✓ Found {len(jobs)} matching jobs.[/green]")
        console.print("[dim]Run [bold]python main.py auto[/bold] to start applying.[/dim]\n")

    def apply_to_job(
        self,
        resume_path: Path,
        job_url: str,
        dry_run: bool = False
    ):
        """Apply to a single job by URL."""
        resume = self._load_resume(resume_path)

        console.print(f"\n[bold]🔍 Analyzing job posting...[/bold]")
        job = self.job_searcher.get_job_from_url(job_url)

        if not job:
            console.print("[red]❌ Could not load job posting. Check the URL.[/red]")
            return

        score = self._score_job(resume, job)
        console.print(f"[bold]📊 Match score:[/bold] {self._score_badge(score)}")

        self._apply_to_single(resume, job, dry_run=dry_run)

    def auto_apply(
        self,
        resume_path: Path,
        role: str,
        location: str,
        limit: int = 5,
        min_score: int = 80,
        dry_run: bool = False
    ):
        """Search for jobs and automatically apply to top matches."""
        if not dry_run:
            console.print(Panel(
                "[yellow]⚠️  AUTO-APPLY MODE[/yellow]\n"
                f"Will submit up to [bold]{limit}[/bold] applications automatically.\n"
                "Review [bold]config.yaml[/bold] to confirm your details are correct.\n\n"
                "Press [bold]Ctrl+C[/bold] to abort.",
                border_style="yellow"
            ))
            time.sleep(3)

        resume = self._load_resume(resume_path)
        
        # If no role specified, extract suitable roles from resume
        if not role:
            role = self._extract_suitable_roles(resume)
            if not role:
                console.print("[red]❌ Could not extract suitable roles from resume.[/red]")
                return
        
        jobs = self._find_matching_jobs(resume, role, location, limit * 3, min_score)

        if not jobs:
            console.print("[yellow]No matching jobs found. Try lowering --min-score.[/yellow]")
            return

        applied = 0
        for job in jobs:
            if applied >= limit:
                break

            already_applied = self.db.get_application(job.url)
            if already_applied:
                console.print(f"[dim]⏭  Already applied to {job.title} at {job.company}[/dim]")
                continue

            success = self._apply_to_single(resume, job, dry_run=dry_run)
            if success:
                applied += 1
                console.print(f"[green]✓ Applied {applied}/{limit}[/green]")
                if applied < limit:
                    delay = self.config.get("apply_delay_seconds", 30)
                    console.print(f"[dim]Waiting {delay}s before next application...[/dim]")
                    time.sleep(delay)

        console.print(Panel(
            f"[bold green]🎉 Done! Submitted {applied} application{'s' if applied != 1 else ''}.[/bold green]\n"
            "Run [bold]python main.py dashboard[/bold] to track your applications.",
            border_style="green"
        ))

    # ─────────────────────────────────────────────
    # INTERNAL HELPERS
    # ─────────────────────────────────────────────

    def _load_resume(self, path: Path) -> Resume:
        """Parse and cache the resume."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task("Parsing resume...", total=None)
            resume = self.resume_parser.parse(path)

        console.print(f"[green]✓ Resume loaded:[/green] {resume.name} | {len(resume.skills)} skills | {len(resume.experience)} roles")
        return resume

    def _find_matching_jobs(
        self, resume: Resume, role: str, location: str, limit: int, min_score: int
    ) -> list[Job]:
        """Search and score jobs."""
        console.print(f"\n[bold]🔍 Searching for [cyan]{role}[/cyan] jobs in [cyan]{location}[/cyan]...[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Fetching job listings...", total=None)
            raw_jobs = self.job_searcher.search(role=role, location=location, limit=limit * 3)
            progress.update(task, description=f"Scoring {len(raw_jobs)} jobs with AI...")
            scored_jobs = self._score_and_filter_jobs(resume, raw_jobs, min_score)

        return scored_jobs[:limit]

    def _score_and_filter_jobs(self, resume: Resume, jobs: list[Job], min_score: int) -> list[Job]:
        """Use Claude to score each job against the resume."""
        scored = []
        for job in jobs:
            job.match_score = self._score_job(resume, job)
            if job.match_score >= min_score:
                scored.append(job)
        scored.sort(key=lambda j: j.match_score, reverse=True)
        return scored

    def _score_job(self, resume: Resume, job: Job) -> int:
        """Ask Claude to score how well resume matches the job (0-100)."""
        try:
            prompt = f"""
Score how well this candidate matches this job posting. Return ONLY a JSON object with two keys:
- "score": integer 0-100
- "reasons": list of 3 short bullet points explaining the score

RESUME SUMMARY:
Name: {resume.name}
Skills: {', '.join(resume.skills[:20])}
Experience: {chr(10).join([f'- {e["title"]} at {e["company"]} ({e["duration"]})' for e in resume.experience[:5]])}
Education: {resume.education}

JOB POSTING:
Title: {job.title}
Company: {job.company}
Location: {job.location}
Description (first 800 chars): {job.description[:800]}

Return only valid JSON, no markdown.
"""
            result = self.claude.complete(prompt, max_tokens=200)
            data = json.loads(result)
            job.match_reasons = data.get("reasons", [])
            return int(data.get("score", 50))
        except Exception:
            return 50

    def _apply_to_single(self, resume: Resume, job: Job, dry_run: bool = False) -> bool:
        """Fill and submit a single job application."""
        console.print(f"\n[bold]📝 Applying to:[/bold] {job.title} @ {job.company}")
        console.print(f"   [dim]{job.url}[/dim]")
        console.print(f"   Match: {self._score_badge(job.match_score)}")

        app = Application(
            job=job,
            resume=resume,
            status=ApplicationStatus.IN_PROGRESS,
            applied_at=datetime.now().isoformat()
        )

        try:
            result = self.form_filler.fill_and_submit(app, dry_run=dry_run)

            if result.success:
                app.status = ApplicationStatus.APPLIED if not dry_run else ApplicationStatus.DRY_RUN
                console.print(f"[green]  ✓ {'[DRY RUN] Would apply' if dry_run else 'Applied successfully!'}[/green]")
            else:
                app.status = ApplicationStatus.FAILED
                app.error = result.error
                console.print(f"[red]  ✗ Failed: {result.error}[/red]")

        except Exception as e:
            app.status = ApplicationStatus.FAILED
            app.error = str(e)
            console.print(f"[red]  ✗ Error: {e}[/red]")

        self.db.save_application(app)
        return app.status in (ApplicationStatus.APPLIED, ApplicationStatus.DRY_RUN)

    def _extract_suitable_roles(self, resume: Resume) -> str:
        """Extract suitable job roles from resume using Claude."""
        console.print("\n[bold]🎯 Analyzing resume to identify suitable roles...[/bold]")
        
        # Prepare experience and skills for Claude
        experience_titles = [exp.get("title", "Unknown") for exp in resume.experience]
        skills_list = ", ".join(resume.skills[:15]) if resume.skills else "Not specified"
        
        prompt = f"""
Based on this professional background, suggest the TOP 3 job titles/roles that would be a good fit.

Experience titles: {', '.join(experience_titles)}
Top skills: {skills_list}
Professional summary: {resume.summary}

Return ONLY a JSON array with exactly 3 role suggestions as strings, e.g. ["Software Engineer", "Full Stack Developer", "Backend Engineer"].
Order by best fit first. Be specific and job-title appropriate.

Return only the JSON array, no explanation.
"""
        try:
            result = self.claude.complete(prompt, max_tokens=200)
            roles = json.loads(result)
            
            if isinstance(roles, list) and len(roles) > 0:
                selected_role = roles[0]
                console.print(f"[green]✓ Suggested roles:[/green] {', '.join(roles)}")
                console.print(f"[cyan]  → Searching for: {selected_role}[/cyan]")
                return selected_role
            else:
                return None
        except Exception as e:
            console.print(f"[yellow]⚠  Could not auto-detect roles: {e}[/yellow]")
            return None

    def _display_jobs_table(self, jobs: list[Job]):
        """Print a rich table of job results."""
        table = Table(title=f"Matching Jobs ({len(jobs)} found)", border_style="cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Title", style="bold white")
        table.add_column("Company", style="cyan")
        table.add_column("Location", style="dim")
        table.add_column("Score", justify="center")
        table.add_column("URL", style="blue dim", no_wrap=True, max_width=40)

        for i, job in enumerate(jobs, 1):
            table.add_row(
                str(i),
                job.title,
                job.company,
                job.location,
                self._score_badge(job.match_score),
                job.url[:40] + "..." if len(job.url) > 40 else job.url
            )

        console.print(table)

    def _score_badge(self, score: int) -> str:
        if score >= 90:
            return f"[bold green]{score}%[/bold green] 🔥"
        elif score >= 75:
            return f"[green]{score}%[/green] ✓"
        elif score >= 60:
            return f"[yellow]{score}%[/yellow]"
        else:
            return f"[red]{score}%[/red]"
