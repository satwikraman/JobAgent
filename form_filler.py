"""
Form Filler - Uses Playwright to automate job application form submission
"""

import time
import json
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from models import Application, ApplicationResult
from claude_client import ClaudeClient
from config import Config


@dataclass
class FillResult:
    success: bool
    error: str = ""
    screenshot_path: str = ""
    confirmation_text: str = ""


class FormFiller:
    """
    Uses Playwright (async → sync wrapper) to:
    1. Navigate to the job application page
    2. Detect and fill form fields intelligently
    3. Handle file uploads (resume)
    4. Answer screening questions using Claude
    5. Submit the form (or skip if dry_run)
    """

    def __init__(self, config: Config, claude: ClaudeClient):
        self.config = config
        self.claude = claude
        self._screenshots_dir = Path("screenshots")
        self._screenshots_dir.mkdir(exist_ok=True)

    def fill_and_submit(self, app: Application, dry_run: bool = False) -> ApplicationResult:
        """Main entry — launches browser, fills form, submits."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "Playwright not installed. Run:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            )

        result = ApplicationResult()

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.config.get("headless", True),
                slow_mo=self.config.get("slow_mo_ms", 50),
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()

            try:
                # Navigate to job page
                page.goto(app.job.url, timeout=30000)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2)

                # Detect apply button and click it
                self._click_apply_button(page)
                time.sleep(2)

                # Handle multi-step application flows
                max_steps = 8
                for step in range(max_steps):
                    filled = self._fill_current_page(page, app)

                    screenshot_path = str(
                        self._screenshots_dir / f"{app.job.company}_{step}.png"
                    )
                    page.screenshot(path=screenshot_path)
                    result.screenshot_path = screenshot_path

                    if not dry_run:
                        advanced = self._click_next_or_submit(page, step)
                        if not advanced:
                            break
                        time.sleep(2)

                        # Check for confirmation
                        conf = self._detect_confirmation(page)
                        if conf:
                            result.confirmation_text = conf
                            result.success = True
                            break
                    else:
                        # Dry run: just log what would be filled
                        result.success = True
                        result.confirmation_text = "DRY RUN - no submission"
                        break

            except Exception as e:
                result.error = str(e)
                result.success = False

            finally:
                browser.close()

        return result

    # ─────────────────────────────────────────────
    # FORM INTERACTION
    # ─────────────────────────────────────────────

    def _click_apply_button(self, page):
        """Find and click the primary apply button."""
        selectors = [
            "button:has-text('Apply Now')",
            "button:has-text('Easy Apply')",
            "button:has-text('Apply')",
            "a:has-text('Apply Now')",
            "a:has-text('Apply')",
            "[aria-label*='apply' i]",
            "#applyButton",
            ".apply-btn",
        ]
        for sel in selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    return
            except Exception:
                continue

    def _fill_current_page(self, page, app: Application) -> bool:
        """
        Intelligently fill all form fields on the current page.
        Returns True if any field was filled.
        """
        resume = app.resume
        job = app.job
        profile = self.config.get("profile", {})
        filled_any = False

        # ── Standard fields ──────────────────────────────
        field_map = {
            # Name
            r"(first.?name|given.?name)": resume.name.split()[0] if resume.name else "",
            r"last.?name": resume.name.split()[-1] if resume.name else "",
            r"full.?name|your.?name": resume.name,
            # Contact
            r"email": resume.email,
            r"phone|mobile|cell": resume.phone,
            # Location
            r"city|location|address": resume.location,
            r"zip|postal": profile.get("zip_code", ""),
            r"state|province": profile.get("state", ""),
            r"country": profile.get("country", "United States"),
            # Links
            r"linkedin": resume.linkedin,
            r"github": resume.github,
            r"portfolio|website|personal": resume.website,
            # Work auth
            r"authorized|eligible|work.?auth": profile.get("work_authorization", "Yes"),
            r"visa|sponsorship": profile.get("requires_sponsorship", "No"),
            # Salary
            r"salary|compensation|expected": profile.get("desired_salary", ""),
            r"notice|start.?date|available": profile.get("notice_period", "2 weeks"),
            # Diversity (optional — configure in config.yaml)
            r"pronouns": profile.get("pronouns", ""),
            r"veteran": profile.get("veteran_status", "I am not a veteran"),
            r"disability": profile.get("disability_status", "I don't wish to answer"),
        }

        inputs = page.locator("input:not([type=hidden]):not([type=submit]):not([type=button])")
        count = inputs.count()

        for i in range(count):
            try:
                inp = inputs.nth(i)
                if not inp.is_visible(timeout=500):
                    continue

                label = self._get_field_label(page, inp)
                input_type = inp.get_attribute("type") or "text"

                if input_type == "file":
                    # Upload resume
                    if resume.file_path and resume.file_path.exists():
                        inp.set_input_files(str(resume.file_path))
                        filled_any = True
                    continue

                if input_type == "checkbox":
                    # Terms/conditions — auto-check
                    if re.search(r"agree|terms|consent|policy", label, re.I):
                        if not inp.is_checked():
                            inp.check()
                    continue

                # Match label to field map
                value = self._match_field(label, field_map)
                if value:
                    inp.fill(value)
                    filled_any = True

            except Exception:
                continue

        # ── Textareas (cover letter, screening questions) ──
        textareas = page.locator("textarea")
        ta_count = textareas.count()

        for i in range(ta_count):
            try:
                ta = textareas.nth(i)
                if not ta.is_visible(timeout=500):
                    continue

                label = self._get_field_label(page, ta)
                existing = ta.input_value()
                if existing.strip():
                    continue  # already filled

                if re.search(r"cover.?letter|why.?apply|why.?interest|motivation", label, re.I):
                    text = self.claude.generate_cover_letter(resume.to_dict(), {"title": job.title, "company": job.company, "description": job.description})
                    ta.fill(text)
                    filled_any = True
                elif label.strip():
                    # Generic screening question
                    answer = self.claude.answer_screening_question(label, resume.to_dict(), {"title": job.title, "company": job.company})
                    ta.fill(answer)
                    filled_any = True

            except Exception:
                continue

        # ── Dropdowns (selects) ──────────────────────────
        selects = page.locator("select")
        sel_count = selects.count()

        for i in range(sel_count):
            try:
                sel = selects.nth(i)
                if not sel.is_visible(timeout=500):
                    continue

                label = self._get_field_label(page, sel)

                if re.search(r"experience|years", label, re.I):
                    yoe = profile.get("years_of_experience", "")
                    if yoe:
                        self._try_select(sel, str(yoe))
                elif re.search(r"education|degree", label, re.I):
                    degree = profile.get("education_level", "Bachelor's Degree")
                    self._try_select(sel, degree)
                elif re.search(r"authorized|work.?auth", label, re.I):
                    self._try_select(sel, "Yes")
                elif re.search(r"sponsorship|visa", label, re.I):
                    self._try_select(sel, "No")

            except Exception:
                continue

        return filled_any

    def _click_next_or_submit(self, page, step: int) -> bool:
        """Click Next or Submit button. Returns False if no button found (end of form)."""
        submit_selectors = [
            "button[type=submit]",
            "button:has-text('Submit')",
            "button:has-text('Submit Application')",
            "input[type=submit]",
        ]
        next_selectors = [
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "button:has-text('Proceed')",
            "button[aria-label*='next' i]",
        ]

        # Try submit first on later steps
        if step > 0:
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=1000):
                        btn.click()
                        return True
                except Exception:
                    continue

        # Try next/continue
        for sel in next_selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=1000):
                    btn.click()
                    return True
            except Exception:
                continue

        return False

    def _detect_confirmation(self, page) -> str:
        """Check if we landed on a confirmation/success page."""
        confirmation_patterns = [
            r"application.*(submitted|received|sent|complete)",
            r"thank.*(you|applying)",
            r"successfully.*(applied|submitted)",
            r"we.*(received|got).*(your|application)",
        ]
        text = page.inner_text("body").lower()
        for pattern in confirmation_patterns:
            if re.search(pattern, text, re.I):
                return text[:200]
        return ""

    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────

    def _get_field_label(self, page, element) -> str:
        """Try to determine the human-readable label for a form field."""
        try:
            # Try aria-label
            aria = element.get_attribute("aria-label") or ""
            if aria:
                return aria

            # Try placeholder
            ph = element.get_attribute("placeholder") or ""
            if ph:
                return ph

            # Try name/id
            name = element.get_attribute("name") or element.get_attribute("id") or ""
            if name:
                return name

            # Try associated <label>
            field_id = element.get_attribute("id")
            if field_id:
                label_el = page.locator(f"label[for='{field_id}']")
                if label_el.count() > 0:
                    return label_el.first.inner_text()

        except Exception:
            pass

        return ""

    def _match_field(self, label: str, field_map: dict) -> str:
        """Find the best matching value for a label using regex patterns."""
        for pattern, value in field_map.items():
            if value and re.search(pattern, label, re.I):
                return value
        return ""

    def _try_select(self, select_el, value: str):
        """Try to select an option by value or label text."""
        try:
            select_el.select_option(label=value)
        except Exception:
            try:
                select_el.select_option(value=value)
            except Exception:
                pass
