"""
Mock Job Data - For testing when Indeed scraping fails
Use this to test the agent without relying on web scraping
"""

from models import Job

MOCK_JOBS = [
    Job(
        title="Senior React Engineer",
        company="TechCorp",
        location="Remote",
        url="https://www.indeed.com/viewjob?jk=mock_001",
        salary="$120,000 - $160,000 per year",
        posted_date="Just posted",
        source="mock",
        easy_apply=False,
        description="Senior React Engineer needed for scaling our web platform..."
    ),
    Job(
        title="Frontend Developer",
        company="StartupXYZ",
        location="Bangalore, India",
        url="https://www.indeed.com/viewjob?jk=mock_002",
        salary="$80,000 - $120,000 per year",
        posted_date="2 days ago",
        source="mock",
        easy_apply=True,
        description="Join our growing team of frontend developers..."
    ),
    Job(
        title="Full Stack Engineer",
        company="Global Tech Inc",
        location="Remote",
        url="https://www.indeed.com/viewjob?jk=mock_003",
        salary="$100,000 - $140,000 per year",
        posted_date="1 week ago",
        source="mock",
        easy_apply=False,
        description="We're looking for experienced full-stack engineers..."
    ),
    Job(
        title="JavaScript Developer",
        company="WebSolutions Ltd",
        location="Remote",
        url="https://www.indeed.com/viewjob?jk=mock_004",
        salary="$70,000 - $110,000 per year",
        posted_date="3 days ago",
        source="mock",
        easy_apply=True,
        description="Help us build the next generation of web applications..."
    ),
    Job(
        title="Mobile Engineer",
        company="AppWorks",
        location="India",
        url="https://www.indeed.com/viewjob?jk=mock_005",
        salary="₹15,00,000 - ₹30,00,000 per year",
        posted_date="1 day ago",
        source="mock",
        easy_apply=False,
        description="Build amazing mobile experiences with React Native..."
    ),
]

def get_mock_jobs(role: str, location: str, limit: int = 5) -> list[Job]:
    """
    Return mock jobs for testing.
    In production, this shouldn't be used.
    """
    # Filter mock jobs by role and location (simple keyword matching)
    filtered = []
    for job in MOCK_JOBS:
        if (role.lower() in job.title.lower() or 
            role.lower() in job.description.lower()):
            filtered.append(job)
    
    return filtered[:limit] if filtered else MOCK_JOBS[:limit]
