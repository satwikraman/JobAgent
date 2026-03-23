"""
Setup Wizard - Interactive first-time configuration
"""

import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()


def run_setup():
    console.print(Panel.fit(
        "[bold cyan]⚙️  Job Agent Setup Wizard[/bold cyan]\n"
        "[dim]Configure your profile for auto-fill[/dim]",
        border_style="cyan"
    ))

    config = {}

    # ── API Key ──────────────────────────────────────────────────────────────
    console.print("\n[bold]Step 1: Gemini API Key[/bold]")
    console.print("[dim]Get your key at https://aistudio.google.com/app/apikey[/dim]")
    api_key = Prompt.ask("Gemini API key", password=True)
    config["google_api_key"] = api_key

    # ── Personal Profile ─────────────────────────────────────────────────────
    console.print("\n[bold]Step 2: Personal Details[/bold]")
    console.print("[dim]Used to auto-fill application forms[/dim]")

    profile = {}
    profile["zip_code"]            = Prompt.ask("ZIP/Postal code")
    profile["state"]               = Prompt.ask("State/Province (e.g. IL)")
    profile["country"]             = Prompt.ask("Country", default="United States")
    profile["work_authorization"]  = Prompt.ask("Authorized to work?", default="Yes")
    profile["requires_sponsorship"]= Prompt.ask("Require visa sponsorship?", default="No")
    profile["desired_salary"]      = Prompt.ask("Desired salary (leave blank to skip)", default="")
    profile["notice_period"]       = Prompt.ask("Notice period / availability", default="2 weeks")
    profile["years_of_experience"] = Prompt.ask("Years of experience (number)", default="")
    profile["education_level"]     = Prompt.ask("Highest education", default="Bachelor's Degree")
    profile["veteran_status"]      = Prompt.ask("Veteran status", default="I am not a veteran")
    profile["disability_status"]   = Prompt.ask("Disability status", default="I don't wish to answer")

    config["profile"] = profile

    # ── Behavior ─────────────────────────────────────────────────────────────
    console.print("\n[bold]Step 3: Agent Behavior[/bold]")
    headless = Confirm.ask("Run browser in headless mode (hidden)?", default=True)
    config["headless"] = headless
    config["slow_mo_ms"] = 50
    config["apply_delay_seconds"] = int(Prompt.ask("Seconds to wait between applications", default="30"))
    config["job_sources"] = ["indeed"]

    # ── Write config ─────────────────────────────────────────────────────────
    config_path = Path("config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    console.print(Panel(
        f"[bold green]✓ Setup complete![/bold green]\n\n"
        f"Config saved to [bold]{config_path}[/bold]\n\n"
        "Next steps:\n"
        "  1. [bold]python main.py search --resume resume.pdf --role 'Software Engineer' --location 'Chicago, IL'[/bold]\n"
        "  2. [bold]python main.py auto --resume resume.pdf --role 'Software Engineer' --dry-run[/bold]\n"
        "  3. [bold]python main.py dashboard[/bold]",
        border_style="green"
    ))
