import asyncio
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from crawler import scrape_jobs
from parser import parse_resume
from matcher import match_jobs

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="DEET-AUTOMATCH API",
    description="Resume parsing, job scraping, and AI-powered job matching.",
    version="1.0.0",
)

_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class Profile(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    skills: list = Field(default_factory=list)
    experience_years: int = 0
    education: str = ""
    previous_roles: list = Field(default_factory=list)
    location: str = ""


class Job(BaseModel):
    title: str
    company: str
    location: str = ""
    skills: list = Field(default_factory=list)
    type: str = "Full-time"
    verified: bool = False


class MatchRequest(BaseModel):
    profile: Profile
    jobs: list


class JobMatchResult(BaseModel):
    title: str
    company: str
    location: str = ""
    skills: list = []
    type: str = ""
    verified: bool = False
    match_score: int
    match_reason: str


class ApplicationRequest(BaseModel):
    applicant_name: str
    applicant_email: str
    cover_note: str
    job_title: str
    job_company: str
    recipient_email: str = ""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/jobs", summary="Fetch available job listings")
async def get_jobs():
    try:
        jobs = await asyncio.to_thread(scrape_jobs)
        logger.info(f"[/jobs] Returning {len(jobs)} jobs")
        return jobs
    except Exception as e:
        logger.error(f"[/jobs] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch jobs")


@app.post("/parse-resume", summary="Upload and parse a resume PDF")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    content = await file.read()

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 5 MB.")

    try:
        profile = await asyncio.to_thread(parse_resume, content)
        logger.info(f"[/parse-resume] Parsed resume: {profile.get('name', 'Unknown')}")
        return profile
    except Exception as e:
        logger.error(f"[/parse-resume] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse resume")


@app.post("/match", summary="Match a profile against jobs")
async def match(data: MatchRequest):
    if not data.jobs:
        raise HTTPException(status_code=400, detail="No jobs provided to match against.")

    try:
        results = await asyncio.to_thread(
            match_jobs,
            data.profile.model_dump(),
            [j if isinstance(j, dict) else j.model_dump() for j in data.jobs],
        )
        logger.info(f"[/match] Matched {len(results)} jobs for {data.profile.name or 'Unknown'}")
        return results
    except Exception as e:
        logger.error(f"[/match] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Failed to match jobs")


@app.post("/apply", summary="Send a job application email")
async def apply_to_job(data: ApplicationRequest):
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        raise HTTPException(
            status_code=500,
            detail="SMTP credentials not configured. Add SMTP_USER and SMTP_PASS to your .env file."
        )

    recipient = data.recipient_email if data.recipient_email else smtp_user

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Application for {data.job_title} at {data.job_company}"
    msg["From"] = smtp_user
    msg["To"] = recipient

    body = f"""
Hi {data.job_company} Hiring Team,

My name is {data.applicant_name} and I am writing to apply for the {data.job_title} position.

{data.cover_note}

Best regards,
{data.applicant_name}
{data.applicant_email}
    """.strip()

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, recipient, msg.as_string())
        logger.info(f"[/apply] Application sent for {data.job_title} at {data.job_company}")
        return {"status": "sent", "message": f"Application sent to {recipient}"}
    except Exception as e:
        logger.error(f"[/apply] Email send failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
