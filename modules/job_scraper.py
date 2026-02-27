"""
Job Scraper — fetches and parses job postings from employer career pages.

Supports:
  - Static HTML pages (requests + BeautifulSoup)
  - Configurable CSS selectors per target site
  - Polite crawling with delays and user-agent rotation
"""

import re
import time
import random
import logging
import hashlib
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1",
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
]

EXPERIENCE_PATTERNS = re.compile(
    r"(\d+)\+?\s*(?:to\s*\d+\s*)?years?"
    r"|entry[\s\-]?level|junior|mid[\s\-]?level|senior|lead|manager",
    re.IGNORECASE,
)

SKILLS_RE = re.compile(
    r"(?:skills?|requirements?|qualifications?)\s*[:\-]?\s*([^\n]{20,300})",
    re.IGNORECASE,
)


def scrape_career_page(target: dict) -> list[dict]:
    """
    Scrape a single career page config and return list of raw job dicts.

    Args:
        target: dict with keys:
            - company, url, job_selector, title_selector,
              location_selector, link_selector
    Returns:
        list of job dicts
    """
    url     = target.get("url", "")
    company = target.get("company", "Unknown")
    logger.info(f"Scraping {company}: {url}")

    try:
        html = _fetch(url)
        if not html:
            return []
        soup = BeautifulSoup(html, "lxml")
        return _parse_jobs(soup, company, url, target)
    except Exception as e:
        logger.error(f"Scrape failed for {url}: {e}")
        return []


def scrape_generic(url: str, company: str = "") -> list[dict]:
    """
    Generic scraper: tries common job-listing selectors across unknown sites.
    """
    try:
        html = _fetch(url)
        if not html:
            return []
        soup  = BeautifulSoup(html, "lxml")
        # Try common selectors
        for selector in [
            ".job", ".job-listing", ".job-post", ".position",
            "[class*='job']", "[class*='vacancy']", "[class*='career']",
            "article", "li.listing",
        ]:
            items = soup.select(selector)
            if items and len(items) >= 2:
                jobs = []
                for item in items[:50]:
                    job = _parse_single_item(item, company, url)
                    if job and job.get("title"):
                        jobs.append(job)
                if jobs:
                    return jobs
        return []
    except Exception as e:
        logger.error(f"Generic scrape failed for {url}: {e}")
        return []


def _fetch(url: str, retries: int = 3) -> str:
    """HTTP GET with retries, random user-agent, and politeness delay."""
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            if resp.status_code == 200:
                return resp.text
            logger.warning(f"HTTP {resp.status_code} for {url} (attempt {attempt+1})")
        except requests.RequestException as e:
            logger.warning(f"Request error: {e} (attempt {attempt+1})")
        time.sleep(random.uniform(1.5, 3.5))
    return ""


def _parse_jobs(soup: BeautifulSoup, company: str, source_url: str, target: dict) -> list[dict]:
    job_selector      = target.get("job_selector", ".job-listing")
    title_selector    = target.get("title_selector", ".job-title")
    location_selector = target.get("location_selector", ".job-location")
    link_selector     = target.get("link_selector", "a")

    items = soup.select(job_selector)
    jobs  = []

    for item in items[:50]:
        title_el    = item.select_one(title_selector)
        location_el = item.select_one(location_selector)
        link_el     = item.select_one(link_selector)

        title    = title_el.get_text(strip=True)    if title_el    else ""
        location = location_el.get_text(strip=True) if location_el else ""
        link     = link_el.get("href", "")          if link_el     else ""

        if not link.startswith("http"):
            from urllib.parse import urljoin
            link = urljoin(source_url, link)

        description = item.get_text(separator=" ", strip=True)

        if not title:
            continue

        job = _build_job_dict(
            title=title,
            company=company,
            location=location,
            description=description,
            application_link=link,
            source_url=source_url,
        )
        jobs.append(job)

    return jobs


def _parse_single_item(item, company: str, source_url: str) -> dict:
    """Parse a single soup element as a job posting."""
    # Try to find a heading element for title
    title_tag = (
        item.find(["h1", "h2", "h3", "h4"])
        or item.find(class_=re.compile(r"title|role|position", re.I))
    )
    title = title_tag.get_text(strip=True) if title_tag else item.get_text(strip=True)[:80]

    location_tag = item.find(class_=re.compile(r"location|city|place", re.I))
    location = location_tag.get_text(strip=True) if location_tag else ""

    link_tag = item.find("a", href=True)
    link = link_tag["href"] if link_tag else source_url
    if not link.startswith("http"):
        from urllib.parse import urljoin
        link = urljoin(source_url, link)

    description = item.get_text(separator=" ", strip=True)

    return _build_job_dict(
        title=title,
        company=company,
        location=location,
        description=description,
        application_link=link,
        source_url=source_url,
    )


def _build_job_dict(title: str, company: str, location: str,
                    description: str, application_link: str,
                    source_url: str) -> dict:
    experience_level = _detect_experience_level(description)
    skills_required  = _extract_required_skills(description)
    content_hash     = _compute_hash(title, company, location)

    return {
        "title":            title.strip(),
        "company":          company.strip(),
        "location":         location.strip(),
        "description":      description[:2000],
        "skills_required":  skills_required,
        "experience_level": experience_level,
        "category":         "Other",           # filled by classifier
        "application_link": application_link,
        "employer_score":   0.0,               # filled by verifier
        "content_hash":     content_hash,
        "source_url":       source_url,
        "is_verified":      False,
    }


def _detect_experience_level(text: str) -> str:
    text_lower = text.lower()
    if any(k in text_lower for k in ["entry level", "entry-level", "junior", "graduate", "fresh"]):
        return "Entry Level"
    if any(k in text_lower for k in ["senior", "lead", "principal", "staff", "7+ year", "8+ year", "10+ year"]):
        return "Senior"
    if any(k in text_lower for k in ["mid level", "mid-level", "3+ year", "4+ year", "5+ year"]):
        return "Mid Level"
    if any(k in text_lower for k in ["manager", "director", "head of", "vp", "executive"]):
        return "Management"
    return "Not Specified"


def _extract_required_skills(description: str) -> list:
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config import SKILLS_KEYWORDS

        desc_lower = description.lower()
        found = []
        for group in SKILLS_KEYWORDS.values():
            for skill in group:
                if re.search(r"\b" + re.escape(skill.lower()) + r"\b", desc_lower):
                    found.append(skill.title())
        return sorted(set(found))[:15]
    except Exception:
        return []


def _compute_hash(title: str, company: str, location: str) -> str:
    raw = f"{title.lower().strip()}|{company.lower().strip()}|{location.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()
