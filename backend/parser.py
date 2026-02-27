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
    "linkedin": "",
    "github": "",
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

    # LinkedIn / GitHub URLs (first occurrence)
    linkedin = ""
    github = ""
    # rough URL regex, then filter by domain
    for match in re.findall(r"(https?://[^\s]+|www\.[^\s]+|linkedin\.com/[^\s]+|github\.com/[^\s]+)", text):
        m = match.strip(".,);]")
        lower = m.lower()
        if not linkedin and "linkedin.com" in lower:
            if not lower.startswith("http"):
                m = "https://" + m.lstrip()
            linkedin = m
        if not github and "github.com" in lower:
            if not lower.startswith("http"):
                m = "https://" + m.lstrip()
            github = m
        if linkedin and github:
            break

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

    # Experience years: look for patterns like "3 years", "5+ years",
    # words like "four years", or lines starting with labels such as
    # "Year of experience".
    experience_years = 0
    exp_match = re.search(r"(\d+)\s*\+?\s*years?", lower_text)
    # also handle number-words (one, two, three...) e.g. "four years experience"
    if not exp_match:
        WORD_NUMS = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
        }
        word_match = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+years?", lower_text)
        if word_match:
            experience_years = WORD_NUMS.get(word_match.group(1), 0)
    if not exp_match and experience_years == 0:
        for ln in lines:
            if ln.lower().startswith("year of experience"):
                num_match = re.search(r"(\d+(\.\d+)?)", ln)
                if num_match:
                    exp_match = num_match
                    break
    if exp_match and experience_years == 0:
        try:
            experience_years = int(float(exp_match.group(1)))
        except ValueError:
            experience_years = 0

    # Education: prefer capturing the block under an "Education" heading,
    # then fall back to scanning for degree keywords.
    education_lines = []
    EDU_KEYWORDS = [
        "bachelor", "master", "b.tech", "btech", "b.e", "be ",
        "m.tech", "mtech", "m.e", "bsc", "msc", "bsc.", "msc.",
        "degree", "bachelor of", "master of",
        "bs in", "ba in",
    ]

    # First: capture the section after an "Education" heading
    for idx, ln in enumerate(lines):
        if ln.strip().lower().startswith("education"):
            for sub in lines[idx + 1 : idx + 10]:
                # stop at next all‑caps heading (e.g. "SKILLS", "EXPERIENCE")
                if sub.isupper() and len(sub.split()) <= 4:
                    break
                if sub:
                    education_lines.append(sub)
            break

    # Fallback/augment: any line mentioning degree keywords
    if not education_lines:
        for ln in lines:
            lower_ln = ln.lower()
            if any(k in lower_ln for k in EDU_KEYWORDS):
                education_lines.append(ln)

    education = " / ".join(dict.fromkeys(education_lines))[:300]

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
        for ln in lines[:20]:
            if any(
                city in ln.lower()
                for city in [
                    "hyderabad",
                    "bangalore",
                    "bengaluru",
                    "mumbai",
                    "pune",
                    "chennai",
                    "delhi",
                    "kolkata",
                    "noida",
                    "gurgaon",
                    "coimbatore",
                ]
            ):
                location = ln.strip()
                break

    # Previous roles: rough extraction from lines under "Experience"/"Employment" headings,
    # and from explicit "Interested Job Function" style lines
    previous_roles = []
    for idx, ln in enumerate(lines):
        if any(h in ln.lower() for h in ["experience", "work history", "employment"]):
            # take a few subsequent lines as potential roles
            for sub in lines[idx + 1: idx + 8]:
                # stop if we hit another section heading
                if sub.isupper() and len(sub.split()) <= 4:
                    break
                # If the line starts with a date range like "1999-2002 ..." strip that off.
                cleaned = re.sub(r"^\s*\d{4}\s*[-–]\s*(\d{4}|present|Present)\s*", "", sub)
                cleaned = cleaned.strip(" -–")
                if cleaned:
                    previous_roles.append(cleaned)
            break

    # If we saw sections like "Interested Job Function" in exported profiles,
    # treat those as previous_roles too
    for ln in lines:
        low = ln.lower()
        if "interested job function" in low or "desired role" in low:
            parts = re.split(r"[:\-]", ln, maxsplit=1)
            if len(parts) == 2:
                role_text = parts[1].strip()
            else:
                role_text = ln.strip()
            if role_text and role_text not in previous_roles:
                previous_roles.append(role_text)

    profile = {
        **EMPTY_PROFILE,
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
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