"""
Job Searcher - Searches Indeed and other job boards for matching positions
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from typing import Optional
from .models import Job
from .config import Config


class JobSearcher:
    """
    Searches job boards for listings. Supports Indeed scraping by default.
    Extend with additional sources as needed.
    """

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def search(self, role: str, location: str, limit: int = 50) -> list[Job]:
        """Search multiple configured sources and combine results."""
        sources = self.config.get("job_sources", ["indeed"])
        all_jobs = []

        for source in sources:
            try:
                if source == "indeed":
                    jobs = self._search_indeed(role, location, limit)
                elif source == "linkedin":
                    jobs = self._search_linkedin(role, location, limit)
                else:
                    continue
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"[yellow]Warning: {source} search failed: {e}[/yellow]")

        # Deduplicate by URL
        seen = set()
        unique = []
        for job in all_jobs:
            if job.url not in seen:
                seen.add(job.url)
                unique.append(job)

        return unique[:limit]

    def get_job_from_url(self, url: str) -> Optional[Job]:
        """Fetch and parse a single job posting from its URL."""
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            if "indeed.com" in url:
                return self._parse_indeed_job_page(url, soup)
            else:
                return self._parse_generic_job_page(url, soup)
        except Exception as e:
            print(f"Error fetching job: {e}")
            return None

    # ─────────────────────────────────────────────
    # INDEED
    # ─────────────────────────────────────────────

    def _search_indeed(self, role: str, location: str, limit: int) -> list[Job]:
        """Scrape Indeed job search results."""
        jobs = []
        start = 0
        per_page = 15

        while len(jobs) < limit:
            url = (
                f"https://www.indeed.com/jobs"
                f"?q={quote_plus(role)}"
                f"&l={quote_plus(location)}"
                f"&start={start}"
                f"&sort=date"
            )

            try:
                resp = self.session.get(url, timeout=15)
                resp.raise_for_status()
            except Exception:
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("div.job_seen_beacon, div[class*='jobCard']")

            if not cards:
                break

            for card in cards:
                job = self._parse_indeed_card(card)
                if job:
                    jobs.append(job)

            if len(cards) < per_page:
                break
            start += per_page

        return jobs[:limit]

    def _parse_indeed_card(self, card) -> Optional[Job]:
        """Parse a single Indeed job card into a Job object."""
        try:
            title_el = card.select_one("h2.jobTitle a, a[id^='job_']")
            company_el = card.select_one("[data-testid='company-name'], span.companyName")
            location_el = card.select_one("[data-testid='text-location'], div.companyLocation")
            salary_el = card.select_one("[data-testid='attribute_snippet_testid']")
            date_el = card.select_one("span[data-testid='myJobsStateDate']")

            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else ""
            location = location_el.get_text(strip=True) if location_el else ""
            salary = salary_el.get_text(strip=True) if salary_el else ""
            posted_date = date_el.get_text(strip=True) if date_el else ""

            # Build job URL
            href = title_el.get("href", "") if title_el else ""
            url = urljoin("https://www.indeed.com", href) if href else ""

            if not title or not url:
                return None

            # Check for Easy Apply
            easy_apply = bool(card.select_one("span[class*='easierapply'], button[aria-label*='Easy Apply']"))

            return Job(
                title=title,
                company=company,
                location=location,
                url=url,
                salary=salary,
                posted_date=posted_date,
                source="indeed",
                easy_apply=easy_apply
            )
        except Exception:
            return None

    def _parse_indeed_job_page(self, url: str, soup: BeautifulSoup) -> Optional[Job]:
        """Parse a full Indeed job detail page."""
        try:
            title = soup.select_one("h1.jobsearch-JobInfoHeader-title")
            company = soup.select_one("[data-testid='inlineHeader-companyName']")
            location = soup.select_one("[data-testid='inlineHeader-companyLocation']")
            description = soup.select_one("#jobDescriptionText")

            return Job(
                title=title.get_text(strip=True) if title else "",
                company=company.get_text(strip=True) if company else "",
                location=location.get_text(strip=True) if location else "",
                url=url,
                description=description.get_text("\n", strip=True) if description else "",
                source="indeed"
            )
        except Exception:
            return None

    def _parse_generic_job_page(self, url: str, soup: BeautifulSoup) -> Optional[Job]:
        """Best-effort parsing for unknown job board pages."""
        title = soup.find("h1")
        body = soup.find("body")

        return Job(
            title=title.get_text(strip=True) if title else "Unknown Title",
            company="",
            location="",
            url=url,
            description=body.get_text("\n", strip=True)[:5000] if body else "",
            source="direct"
        )

    # ─────────────────────────────────────────────
    # LINKEDIN (stub — requires auth or Rapid API)
    # ─────────────────────────────────────────────

    def _search_linkedin(self, role: str, location: str, limit: int) -> list[Job]:
        """
        LinkedIn job search stub.
        Implement using RapidAPI LinkedIn Jobs endpoint or Playwright-based auth.
        See README.md for setup instructions.
        """
        return []
