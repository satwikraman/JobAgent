"""
Job Searcher - Searches Indeed and other job boards for matching positions
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from typing import Optional
from models import Job
from config import Config


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
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.indeed.com/",
    }

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def search(self, role: str, location: str, limit: int = 50) -> list[Job]:
        """Search multiple configured sources and combine results."""
        sources = self.config.get("job_sources", ["indeed"])
        all_jobs = []
        use_mock = False

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
        
        # Fallback to mock jobs if no real jobs found
        if not all_jobs:
            try:
                from mock_jobs import get_mock_jobs
                print(f"[yellow]💡 Using mock job data for demonstration (Indeed scraping blocked)[/yellow]")
                all_jobs = get_mock_jobs(role, location, limit * 2)
                use_mock = True
            except ImportError:
                pass

        # Deduplicate by URL
        seen = set()
        unique = []
        for job in all_jobs:
            if job.url not in seen:
                seen.add(job.url)
                unique.append(job)

        if use_mock and unique:
            for job in unique:
                if not hasattr(job, 'source'):
                    job.source = "mock"

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
        import time
        jobs = []
        start = 0
        per_page = 15
        use_playwright = False

        while len(jobs) < limit:
            url = (
                f"https://www.indeed.com/jobs"
                f"?q={quote_plus(role)}"
                f"&l={quote_plus(location)}"
                f"&start={start}"
                f"&sort=date"
            )

            try:
                # Add delay to avoid getting blocked
                if start > 0:
                    time.sleep(1)
                
                # Try regular HTTP first
                if not use_playwright:
                    resp = self.session.get(url, timeout=15)
                    
                    if resp.status_code == 403:
                        # Fallback to Playwright for JavaScript rendering
                        print(f"[yellow]Indeed blocked HTTP request. Attempting with browser automation...[/yellow]")
                        use_playwright = True
                        # Try again with Playwright
                        soup = self._fetch_with_playwright(url)
                        if not soup:
                            break
                    else:
                        resp.raise_for_status()
                        soup = BeautifulSoup(resp.text, "html.parser")
                else:
                    soup = self._fetch_with_playwright(url)
                    if not soup:
                        break
                        
            except Exception as e:
                print(f"[yellow]Warning: Failed to fetch Indeed page at {start}: {e}[/yellow]")
                break

            # Try multiple selector patterns as Indeed changes HTML structure
            cards = soup.select("div.job_seen_beacon, div[class*='jobCard'], li[id*='job_'], div[class*='result']")
            
            if not cards:
                # Log what we actually got for debugging
                print(f"[yellow]Warning: No job cards found on page.[/yellow]")
                break

            for card in cards:
                job = self._parse_indeed_card(card)
                if job:
                    jobs.append(job)

            if len(cards) < per_page:
                break
            start += per_page

        if not jobs and start == 0:
            print(f"[yellow]💡 Tip: Indeed is blocking scrapers. Workarounds:[/yellow]")
            print(f"[yellow]   1. Make sure Playwright is installed: playwright install chromium[/yellow]")
            print(f"[yellow]   2. Try a different job board or extend with custom scrapers[/yellow]")
            print(f"[yellow]   3. Increase delays in config.yaml for slow_mo_ms[/yellow]")
        
        return jobs[:limit]

    def _fetch_with_playwright(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch page using Playwright browser automation as fallback."""
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers(self.HEADERS)
                page.goto(url, wait_until="networkidle")
                
                # Wait for job cards to load
                page.wait_for_selector("div.job_seen_beacon, div[class*='jobCard']", timeout=5000)
                
                content = page.content()
                browser.close()
                
                return BeautifulSoup(content, "html.parser")
        except ImportError:
            print(f"[yellow]Warning: Playwright not installed. Install with: pip install playwright; playwright install chromium[/yellow]")
            return None
        except Exception as e:
            print(f"[yellow]Warning: Playwright fetch failed: {e}[/yellow]")
            return None

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
