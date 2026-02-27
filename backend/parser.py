import io
import logging
import re
from pathlib import Path

import pdfplumber

# spaCy is optional – if it isn't installed, we just use heuristics
try:
    import spacy  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    spacy = None

logger = logging.getLogger(__name__)


EMPTY_PROFILE = {
    "name": "",
    "email": "",
    "phone": "",
    "skills": [],
    "experience_years": 0,
    "education": "",
    "previous_roles": [],
    "location": "",
}

# Directory where your trained spaCy model is stored (from train_resume_ner.py)
MODEL_DIR = Path("models/resume_ner")
_nlp = None


def _get_model():
    """
    Lazy‑load the trained spaCy model from disk.
    Returns None if spaCy isn't available or the model isn't on disk.
    """
    global _nlp
    if spacy is None:
        logger.info("[parser] spaCy not installed – skipping model parsing")
        return None

    if _nlp is None:
        try:
            _nlp = spacy.load(MODEL_DIR)
        except Exception as e:
            logger.warning(f"[parser] Could not load spaCy model at {MODEL_DIR}: {e}")
            return None
    return _nlp


def parse_resume(file_bytes: bytes) -> dict:
    """
    Parse a resume PDF using a locally trained spaCy NER model.
    Falls back to heuristic parsing if the model is unavailable.
    """
    try:
        raw_text = extract_text(file_bytes)
    except Exception as e:
        logger.error(f"[parser] Failed to extract text from PDF: {e}")
        return {**EMPTY_PROFILE, "name": "Could not parse — invalid or unreadable PDF"}

    if not raw_text.strip():
        logger.warning("[parser] PDF text extraction returned empty content")
        return {**EMPTY_PROFILE, "name": "Could not parse — empty PDF"}

    # First try the trained model, if available
    nlp = _get_model()
    if nlp is not None:
        try:
            doc = nlp(raw_text)
            profile = build_profile_from_model(doc, raw_text)
            logger.info(f"[parser] Model‑parsed resume for: {profile.get('name') or 'Unknown'}")
            return profile
        except Exception as e:
            logger.error(f"[parser] Model parse failed, falling back to heuristics: {e}")

    # Fallback: simple regex‑based heuristics (no ML)
    profile = build_profile_from_text(raw_text)
    logger.info(f"[parser] Heuristically parsed resume for: {profile.get('name') or 'Unknown'}")
    return profile


def build_profile_from_model(doc, text: str) -> dict:
    """
    Build a profile from spaCy NER entities.
    Expected labels in the trained model: NAME, EMAIL, PHONE, SKILL, LOCATION.
    """
    name = ""
    email = ""
    phone = ""
    location = ""
    skills = set()

    for ent in doc.ents:
        if ent.label_ == "NAME" and not name:
            name = ent.text.strip()
        elif ent.label_ == "EMAIL" and not email:
            email = ent.text.strip()
        elif ent.label_ == "PHONE" and not phone:
            phone = ent.text.strip()
        elif ent.label_ == "LOCATION" and not location:
            location = ent.text.strip()
        elif ent.label_ == "SKILL":
            skills.add(ent.text.strip())

    # You can still derive these from text with heuristics if you want
    heuristics = build_profile_from_text(text)

    profile = {
        **EMPTY_PROFILE,
        "name": name or heuristics["name"],
        "email": email or heuristics["email"],
        "phone": phone or heuristics["phone"],
        "location": location or heuristics["location"],
        "skills": sorted(skills) or heuristics["skills"],
        "experience_years": heuristics["experience_years"],
        "education": heuristics["education"],
        "previous_roles": heuristics["previous_roles"],
    }
    return profile


def build_profile_from_text(text: str) -> dict:
    """
    Very simple heuristic parser for common resume fields.
    This is not as powerful as an LLM but avoids external dependencies.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln and ln.strip()]
    lower_text = text.lower()

    # Email
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    email = email_match.group(0) if email_match else ""

    # Phone (very rough)
    phone_match = re.search(r"(\+?\d[\d\-\s]{7,}\d)", text)
    phone = phone_match.group(0).strip() if phone_match else ""

    # Name: first non-empty line that doesn't look like a heading or contact line
    name = ""
    for ln in lines[:8]:
        lower_ln = ln.lower()
        if email and email in ln:
            continue
        if any(k in lower_ln for k in ["resume", "curriculum vitae", "cv", "phone", "email", "contact"]):
            continue
        # short-ish line with a few words is likely the name
        if 2 <= len(ln.split()) <= 6:
            name = ln
            break

    # Skills: intersect with a known skills list
    KNOWN_SKILLS = [
        "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js",
        "SQL", "MySQL", "PostgreSQL", "MongoDB",
        "HTML", "CSS", "Django", "Flask", "FastAPI",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes",
        "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch",
        "Power BI", "Tableau", "Excel", "Git", "Linux",
        "Machine Learning", "Data Analysis",
    ]
    found_skills = []
    for s in KNOWN_SKILLS:
        if re.search(r"\b" + re.escape(s) + r"\b", text, flags=re.IGNORECASE):
            found_skills.append(s)
    # preserve order and uniqueness
    skills = list(dict.fromkeys(found_skills))

    # Experience years: look for patterns like "3 years", "5+ years"
    experience_years = 0
    exp_match = re.search(r"(\d+)\s*\+?\s*years?", lower_text)
    if exp_match:
        try:
            experience_years = int(exp_match.group(1))
        except ValueError:
            experience_years = 0

    # Education: capture lines mentioning common degree keywords
    education_lines = []
    EDU_KEYWORDS = [
        "bachelor", "master", "b.tech", "btech", "b.e", "be ",
        "m.tech", "mtech", "m.e", "bsc", "msc", "bsc.", "msc.",
        "degree", "bachelor of", "master of",
    ]
    for ln in lines:
        lower_ln = ln.lower()
        if any(k in lower_ln for k in EDU_KEYWORDS):
            education_lines.append(ln)
    education = " / ".join(dict.fromkeys(education_lines))[:250]

    # Location: look for a "Location" line or address-style line
    location = ""
    for ln in lines[:15]:
        lower_ln = ln.lower()
        if "location" in lower_ln:
            # e.g., "Location: Hyderabad, India"
            parts = ln.split(":", 1)
            location = parts[1].strip() if len(parts) == 2 else ln.strip()
            break
    # fallback: last token of a contact-looking line
    if not location:
        for ln in lines[:15]:
            if any(city in ln.lower() for city in ["hyderabad", "bangalore", "bengaluru", "mumbai", "pune", "chennai", "delhi"]):
                location = ln.strip()
                break

    # Previous roles: rough extraction from lines under "Experience" headings
    previous_roles = []
    for idx, ln in enumerate(lines):
        if any(h in ln.lower() for h in ["experience", "work history", "employment"]):
            # take a few subsequent lines as potential roles
            for sub in lines[idx + 1: idx + 8]:
                # stop if we hit another section heading
                if sub.isupper() and len(sub.split()) <= 4:
                    break
                if re.search(r"\b(developer|engineer|analyst|manager|intern|consultant|lead)\b", sub, flags=re.IGNORECASE):
                    previous_roles.append(sub.strip())
            break

    profile = {
        **EMPTY_PROFILE,
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "experience_years": experience_years,
        "education": education,
        "previous_roles": previous_roles,
        "location": location,
    }
    return profile


def extract_text(file_bytes: bytes) -> str:
    if not file_bytes.startswith(b"%PDF"):
        raise ValueError("Uploaded file does not appear to be a valid PDF.")
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        if len(pdf.pages) == 0:
            raise ValueError("PDF has no pages.")
        return "\n".join(page.extract_text() or "" for page in pdf.pages)