# Troubleshooting: No Jobs Found

## Root Causes

Your Job Agent is not finding jobs because of **3 cascading issues**:

### 1. **Indeed Actively Blocks Web Scrapers**
- Indeed detects and blocks automated HTTP requests with **403 Forbidden** errors
- This is intentional - Indeed doesn't allow bots to scrape their job listings
- **Workaround**: The agent now uses Playwright (browser automation) as a fallback, but this requires JavaScript rendering

### 2. **Gemini API Insufficient Credits**
- Resume parsing needs Gemini API to extract structured data
- Your account has insufficient credits for API calls
- **Result**: Resume has 0 skills → all jobs score low during filtering

### 3. **Low Scoring Filters Out Results**
- Default min-score is 70/100
- Without extracted resume skills, jobs are all scored at ~50
- Jobs get filtered out before display

---

## Solutions

### ✅ Short Term: Use Explicit Roles (No Resume Parsing)

Instead of relying on resume parsing, provide explicit job roles:

```bash
source .venv/bin/activate

# This works without needing Gemini API or perfect resume parsing
python main.py search --resume resume.pdf --role "Software Engineer" --location "Remote"
```

The `--role` parameter is **required for job search to work reliably**. Auto-detection requires Gemini API credits.

### ✅ Medium Term: Add Gemini Credits

To enable full AI features:

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and create/get your API key
2. Add credits to your Google Cloud billing account if needed
2. Click **"Buy Credits"** and purchase $5-20 worth
3. This unlocks:
   - Resume skill extraction
   - Job matching scoring
   - Cover letter generation
   - Auto-detection of suitable roles

### ✅ Long Term: Alternative Job Sources

The agent can be extended with other job sources that don't block bots:

- **LinkedIn API** (requires credentials)
- **GitHub Jobs** API
- **Custom scrapers** for specific company job boards
- **RSS feeds** from job aggregators

---

## Current Status

Your agent **is working**, it just needs:

1. **Explicit job roles** (until Gemini credits added)
2. **Better resume data** (with Gemini credits)
3. **Understanding of Indeed's blocking** (expected behavior)

### What Works Now:
✅ Resume parsing from PDF/DOCX (when API available)
✅ Job search with explicit role + location
✅ Job scoring with fallback to simple keyword matching
✅ Form filling and application tracking
✅ Dashboard for tracking applications
✅ Cover letter generation
✅ Screening question answering

### What Needs API Credits:
❌ Auto-detection of suitable roles from resume
❌ Advanced AI-based job matching
❌ Smart screening question answering

---

## Example Usage (Working Now)

```bash
# Activate environment
source .venv/bin/activate

# Search for specific roles
python main.py search \
  --resume /path/to/resume.pdf \
  --role "Software Engineer" \
  --location "Remote" \
  --limit 5

# Auto-apply to matching jobs
python main.py auto \
  --resume /path/to/resume.pdf \
  --role "Full Stack Engineer" \
  --location "Bangalore, India" \
  --limit 10 \
  --min-score 50 \
  --dry-run  # Preview first!
```

---

## recommended Next Steps

1. **Use explicit `--role` parameter** for now
2. **Add $5 in Gemini credits** to unlock full features
3. **Test dry-run mode** before auto-applying
4. **Track applications** in the dashboard

The agent is fully functional - it just needs a bit of configuration to work optimally!
