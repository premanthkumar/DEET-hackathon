"""
Confidence Scorer — assigns per-field confidence scores to extracted data.

Score levels:
  1.0  — regex-validated (email, phone with format check)
  0.88 — spaCy NER match
  0.72 — heuristic / partial NER
  0.45 — section-based extraction
  0.0  — field missing / empty
"""

import re
from typing import Any


EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
PHONE_RE = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")


def score_profile(profile: dict) -> dict:
    """
    Takes a raw extracted profile dict and returns a scores dict
    mapping field name → confidence float.
    """
    scores = {}

    scores["full_name"]       = _score_name(profile.get("full_name", ""))
    scores["email"]           = _score_email(profile.get("email", ""))
    scores["phone"]           = _score_phone(profile.get("phone", ""))
    scores["address"]         = _score_text_field(profile.get("address", ""), min_len=5)
    scores["linkedin"]        = _score_url(profile.get("linkedin", ""))
    scores["github"]          = _score_url(profile.get("github", ""))
    scores["summary"]         = _score_text_field(profile.get("summary", ""), min_len=30)
    scores["education"]       = _score_list_field(profile.get("education", []))
    scores["skills"]          = _score_list_field(profile.get("skills", []), min_items=3)
    scores["certifications"]  = _score_list_field(profile.get("certifications", []))
    scores["work_experience"] = _score_list_field(profile.get("work_experience", []))
    scores["projects"]        = _score_list_field(profile.get("projects", []))

    scores["overall"] = _compute_overall(scores)
    return scores


def _score_name(value: str) -> float:
    if not value or len(value.strip()) < 2:
        return 0.0
    parts = value.split()
    if 2 <= len(parts) <= 5 and all(p[0].isupper() for p in parts if p):
        return 0.88   # Well-formed name
    if len(parts) == 1 and value[0].isupper():
        return 0.55   # Single word
    return 0.35


def _score_email(value: str) -> float:
    if not value:
        return 0.0
    return 1.0 if EMAIL_RE.match(value.strip()) else 0.40


def _score_phone(value: str) -> float:
    if not value:
        return 0.0
    digits = re.sub(r"\D", "", value)
    if 7 <= len(digits) <= 15 and PHONE_RE.match(value.strip()):
        return 1.0
    if 7 <= len(digits) <= 15:
        return 0.72
    return 0.25


def _score_url(value: str) -> float:
    if not value:
        return 0.0
    if value.startswith("http"):
        return 0.95
    return 0.50


def _score_text_field(value: str, min_len: int = 5) -> float:
    if not value or len(value.strip()) < min_len:
        return 0.0
    length = len(value.strip())
    if length >= 100:
        return 0.80
    if length >= 30:
        return 0.65
    return 0.45


def _score_list_field(value: list, min_items: int = 1) -> float:
    if not value or len(value) < min_items:
        return 0.0
    if len(value) >= 5:
        return 0.85
    if len(value) >= 2:
        return 0.70
    return 0.50


def _compute_overall(scores: dict) -> float:
    """Weighted average of field scores (important fields weighted more)."""
    weights = {
        "full_name":       3.0,
        "email":           3.0,
        "phone":           2.0,
        "skills":          2.5,
        "work_experience": 2.5,
        "education":       2.0,
        "address":         1.0,
        "summary":         1.0,
        "certifications":  1.0,
        "projects":        1.0,
        "linkedin":        0.5,
        "github":          0.5,
    }
    total_weight = 0.0
    total_score  = 0.0
    for field, weight in weights.items():
        if field in scores:
            total_score  += scores[field] * weight
            total_weight += weight

    return round(total_score / total_weight, 3) if total_weight > 0 else 0.0


def get_confidence_label(score: float) -> str:
    """Human-readable label for a confidence score."""
    if score >= 0.85:
        return "high"
    elif score >= 0.55:
        return "medium"
    elif score > 0.0:
        return "low"
    else:
        return "missing"
