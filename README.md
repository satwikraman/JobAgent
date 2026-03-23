# 🤖 AI Job Application Agent

An AI-powered local agent that reads your resume, searches for matching jobs, auto-fills applications, and tracks everything in a dashboard — powered by Gemini AI.

---

## 📄 Resume

👉 **[View & Download Resume](./RESUME.md)** — Hosted on GitHub

Your resume is now publicly accessible at:
```
https://raw.githubusercontent.com/satwikramantarlana/JobAgent/main/resume.pdf
```

Use this link in job applications, LinkedIn, and portfolio sites.

---

## Features

- **Resume parsing** — Extracts structured data from PDF, DOCX, or TXT resumes using Gemini
- **Job search** — Scrapes Indeed for matching roles (LinkedIn support optional)
- **AI match scoring** — Gemini scores each job 0–100 based on your resume fit
- **Browser automation** — Playwright fills and submits application forms automatically
- **Cover letter generation** — Gemini writes a tailored cover letter for each application
- **Screening questions** — Gemini answers free-text questions based on your background
- **Application tracking** — SQLite database + Streamlit dashboard
- **Dry-run mode** — Preview everything without submitting

---

## Quick Start

### 1. Install dependencies

```bash
# Create virtual environment (first time only)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 2. Run the setup wizard

```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate

python main.py setup
```

This creates `config.yaml` with your profile and API key.

Alternatively, copy `config.yaml` and fill in your details manually, or set:
```bash
export GOOGLE_API_KEY=your_google_api_key_here
```

### 3. Search for jobs

**Option A: Auto-detect suitable roles from your resume**

```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate

python main.py search \
  --resume resume.pdf \
  --location "Chicago, IL"
```

The agent will analyze your resume and suggest 3 suitable job roles, then search for jobs matching the top suggestion.

**Option B: Specify a role explicitly**

```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate

python main.py search \
  --resume resume.pdf \
  --role "Software Engineer" \
  --location "Chicago, IL"
```

### 4. Dry run (preview without submitting)

**Option A: Auto-detect roles from resume**

```bash
python main.py auto \
  --resume resume.pdf \
  --location "Remote" \
  --limit 3 \
  --dry-run
```

**Option B: Specify a role**

```bash
python main.py auto \
  --resume resume.pdf \
  --role "Data Scientist" \
  --location "Remote" \
  --limit 3 \
  --dry-run
```

### 5. Auto-apply

**Option A: Auto-detect roles from resume**

```bash
python main.py auto \
  --resume resume.pdf \
  --location "Chicago, IL" \
  --limit 10 \
  --min-score 80
```

**Option B: Specify a role**

```bash
python main.py auto \
  --resume resume.pdf \
  --role "Software Engineer" \
  --location "Chicago, IL" \
  --limit 10 \
  --min-score 80
```

### 6. Apply to a specific job

```bash
python main.py apply \
  --resume resume.pdf \
  --job-url "https://www.indeed.com/viewjob?jk=abc123"
```

### 7. Launch the dashboard

```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate

python main.py dashboard
# Opens http://localhost:8501
```

---

## Configuration

Edit `config.yaml` to configure:

| Key | Description |
|-----|-------------|
| `google_api_key` | Your Gemini API key |
| `headless` | `true` = hidden browser, `false` = visible |
| `slow_mo_ms` | Milliseconds between actions (increase if sites block you) |
| `apply_delay_seconds` | Wait between applications |
| `job_sources` | `["indeed"]` or add `"linkedin"` |
| `profile.*` | Personal details for auto-fill |

---

## How It Works

```
Your Resume (PDF/DOCX)
        │
        ▼
┌──────────────────┐
│  Resume Parser   │  ← Gemini extracts skills, experience, contact info
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Job Searcher   │  ← Scrapes Indeed for matching roles
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  AI Match Scorer │  ← Gemini scores each job 0-100
└────────┬─────────┘
         │ (filtered by --min-score)
         ▼
┌──────────────────┐
│   Form Filler    │  ← Playwright fills forms field-by-field
│                  │  ← Gemini writes cover letters & answers questions
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│    Database      │  ← SQLite tracks every application
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Dashboard      │  ← Streamlit UI to track status, interviews, offers
└──────────────────┘
```

---

## Tips

- **Auto-detect job roles** — Omit `--role` and the agent will analyze your resume to suggest suitable positions
- **Always activate the virtual environment** first: `source .venv/bin/activate`
- **Start with `--dry-run`** to see what the agent would do before submitting real applications
- **Set `headless: false`** to watch the browser and debug any issues
- **Increase `slow_mo_ms`** (e.g. 200) if sites are detecting automation
- **Set `--min-score 85`** for strict matching; `70` for more applications
- **Update application status** manually in the dashboard after interviews/rejections

---

## Limitations & Notes

- **Indeed scraping** — Indeed actively blocks automated requests. If you get `403 Forbidden` errors:
  - Try using a broad location like "India" or "Remote" instead of specific cities
  - Indeed may require additional delays. You can increase `slow_mo_ms` in `config.yaml` to add inter-request delays
  - Be a good citizen: use reasonable delays (15+ seconds between requests) to avoid getting your IP blocked permanently
  - Best jobs with an "Apply Now" redirect to employer sites work well. Indeed's own "Easy Apply" flow requires additional handling.
- **Multi-step forms** — Workday, Greenhouse, Lever and other ATS platforms are supported but complex flows may require manual completion.
- **CAPTCHA** — If you encounter CAPTCHAs, set `headless: false` in config.yaml and solve them manually. Consider adding delays.
- **Rate limits** — Don't set `apply_delay_seconds` below 15; some sites will block you.
- **LinkedIn** — Full support requires LinkedIn account credentials or a paid RapidAPI key. See `job_searcher.py` for the stub.

---

## Project Structure

```
job-agent/
├── main.py                  # CLI entry point
├── config.yaml              # Your configuration
├── requirements.txt
├── applications.db          # SQLite database (auto-created)
├── screenshots/             # Screenshots of each application step
└── agent/
    ├── agent.py             # Core orchestrator
    ├── gemini_client.py     # Google Gemini API wrapper
    ├── resume_parser.py     # PDF/DOCX → structured data
    ├── job_searcher.py      # Indeed scraper
    ├── form_filler.py       # Playwright browser automation
    ├── database.py          # SQLite persistence
    ├── config.py            # Config loader
    ├── models.py            # Data models
    ├── dashboard.py         # Dashboard launcher
    ├── dashboard_app.py     # Streamlit dashboard
    └── setup_wizard.py      # First-time setup
```
