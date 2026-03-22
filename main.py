#!/usr/bin/env python3
"""
Job Application Agent - Main Entry Point
Run: python main.py --help
"""

import argparse
import sys
from pathlib import Path
from agent.agent import JobAgent
from agent.dashboard import launch_dashboard

def main():
    parser = argparse.ArgumentParser(
        description="🤖 AI Job Application Agent - Auto-find and apply to jobs using your resume",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py search --resume resume.pdf --role "Software Engineer" --location "Chicago, IL"
  python main.py apply --job-url "https://www.indeed.com/viewjob?jk=abc123"
  python main.py auto --resume resume.pdf --role "Data Scientist" --limit 10
  python main.py dashboard
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # --- search command ---
    search_parser = subparsers.add_parser("search", help="Search for matching jobs")
    search_parser.add_argument("--resume", required=True, help="Path to your resume (PDF or DOCX)")
    search_parser.add_argument("--role", required=True, help="Job title/role to search for")
    search_parser.add_argument("--location", default="Remote", help="Job location (default: Remote)")
    search_parser.add_argument("--limit", type=int, default=20, help="Max jobs to find (default: 20)")
    search_parser.add_argument("--min-score", type=int, default=70, help="Min match score 0-100 (default: 70)")

    # --- apply command ---
    apply_parser = subparsers.add_parser("apply", help="Apply to a specific job URL")
    apply_parser.add_argument("--resume", required=True, help="Path to your resume (PDF or DOCX)")
    apply_parser.add_argument("--job-url", required=True, help="Direct URL to the job posting")
    apply_parser.add_argument("--dry-run", action="store_true", help="Preview form fill without submitting")

    # --- auto command ---
    auto_parser = subparsers.add_parser("auto", help="Automatically search AND apply to matching jobs")
    auto_parser.add_argument("--resume", required=True, help="Path to your resume (PDF or DOCX)")
    auto_parser.add_argument("--role", required=True, help="Job title/role to search for")
    auto_parser.add_argument("--location", default="Remote", help="Job location (default: Remote)")
    auto_parser.add_argument("--limit", type=int, default=5, help="Max applications to submit (default: 5)")
    auto_parser.add_argument("--min-score", type=int, default=80, help="Min match score to auto-apply (default: 80)")
    auto_parser.add_argument("--dry-run", action="store_true", help="Preview without submitting")

    # --- dashboard command ---
    dash_parser = subparsers.add_parser("dashboard", help="Launch the web dashboard to track applications")
    dash_parser.add_argument("--port", type=int, default=8501, help="Port for dashboard (default: 8501)")

    # --- setup command ---
    setup_parser = subparsers.add_parser("setup", help="Interactive setup wizard")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "setup":
        from agent.setup_wizard import run_setup
        run_setup()

    elif args.command == "dashboard":
        launch_dashboard(port=args.port)

    elif args.command == "search":
        agent = JobAgent()
        resume_path = Path(args.resume)
        if not resume_path.exists():
            print(f"❌ Resume not found: {resume_path}")
            sys.exit(1)
        agent.search_jobs(
            resume_path=resume_path,
            role=args.role,
            location=args.location,
            limit=args.limit,
            min_score=args.min_score
        )

    elif args.command == "apply":
        agent = JobAgent()
        resume_path = Path(args.resume)
        if not resume_path.exists():
            print(f"❌ Resume not found: {resume_path}")
            sys.exit(1)
        agent.apply_to_job(
            resume_path=resume_path,
            job_url=args.job_url,
            dry_run=args.dry_run
        )

    elif args.command == "auto":
        agent = JobAgent()
        resume_path = Path(args.resume)
        if not resume_path.exists():
            print(f"❌ Resume not found: {resume_path}")
            sys.exit(1)
        agent.auto_apply(
            resume_path=resume_path,
            role=args.role,
            location=args.location,
            limit=args.limit,
            min_score=args.min_score,
            dry_run=args.dry_run
        )

if __name__ == "__main__":
    main()
