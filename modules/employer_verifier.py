"""
Employer Verifier — scores the authenticity of employer domains.

Checks:
  1. DNS A record resolution
  2. WHOIS domain age (>= 180 days = trusted)
  3. HTTP reachability
  4. Known fake/spam domain block-list check
  5. HTTPS presence

Score: 0.0 – 1.0 (higher = more trustworthy)
"""

import re
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

KNOWN_SPAM_DOMAINS = {
    "fakejobs.com", "scamjobs.net", "freelancescam.biz",
    "workathomefake.com", "earnmoneynow.biz",
}

MIN_DOMAIN_AGE_DAYS = 180


def verify_employer(url: str) -> dict:
    """
    Full employer verification for a given URL.

    Returns:
        {
            "domain": str,
            "score": float,           # 0.0–1.0
            "is_trusted": bool,
            "checks": {               # individual check results
                "dns": bool,
                "reachable": bool,
                "https": bool,
                "domain_age_days": int | None,
                "not_spam": bool,
            }
        }
    """
    domain = _extract_domain(url)
    if not domain:
        return _result(domain="", score=0.0, checks={})

    checks = {
        "dns":             _check_dns(domain),
        "reachable":       False,
        "https":           url.startswith("https://"),
        "domain_age_days": None,
        "not_spam":        domain not in KNOWN_SPAM_DOMAINS,
    }

    if checks["dns"]:
        checks["reachable"] = _check_reachable(url)
        checks["domain_age_days"] = _check_domain_age(domain)

    score = _compute_score(checks)
    return _result(domain=domain, score=score, checks=checks)


def _extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url if url.startswith("http") else f"http://{url}")
        return parsed.netloc.replace("www.", "").lower().strip()
    except Exception:
        return ""


def _check_dns(domain: str) -> bool:
    try:
        import socket
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False


def _check_reachable(url: str) -> bool:
    try:
        import requests
        resp = requests.head(url, timeout=8, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0"})
        return resp.status_code < 500
    except Exception:
        return False


def _check_domain_age(domain: str) -> int | None:
    """Returns age in days or None if WHOIS fails."""
    try:
        import whois
        w = whois.whois(domain)
        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        if creation:
            # Handle both naive and aware datetimes
            if hasattr(creation, "replace"):
                now = datetime.now()
                age = (now - creation.replace(tzinfo=None)).days
                return max(age, 0)
    except Exception as e:
        logger.debug(f"WHOIS lookup failed for {domain}: {e}")
    return None


def _compute_score(checks: dict) -> float:
    score = 0.0

    # Hard fails
    if not checks.get("not_spam"):
        return 0.0
    if not checks.get("dns"):
        return 0.05

    # Positive signals
    if checks.get("dns"):        score += 0.25
    if checks.get("reachable"):  score += 0.25
    if checks.get("https"):      score += 0.20

    age = checks.get("domain_age_days")
    if age is not None:
        if age >= 365:
            score += 0.30
        elif age >= MIN_DOMAIN_AGE_DAYS:
            score += 0.20
        elif age >= 60:
            score += 0.05
        # Very new domain: no bonus

    return round(min(score, 1.0), 3)


def _result(domain: str, score: float, checks: dict) -> dict:
    return {
        "domain":     domain,
        "score":      score,
        "is_trusted": score >= 0.6,
        "checks":     checks,
    }
