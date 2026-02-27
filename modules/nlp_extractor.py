"""
NLP Extraction Pipeline — extracts structured DEET profile fields from raw resume text.

Pipeline stages:
  1. Text normalization
  2. Section detection (regex headers)
  3. Named Entity Recognition (spaCy)
  4. Pattern matching (email, phone, LinkedIn)
  5. Skills extraction (keyword dictionary)
  6. Date normalization
"""

import re
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── spaCy lazy loader ──────────────────────────────────────────────────────────

_nlp = None

def _get_nlp():
    """
    Lazy-load spaCy model. Returns None on any failure so the pipeline
    falls back to regex-only extraction (handles Python 3.14 + spaCy
    REGEX attribute incompatibility gracefully).
    """
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            _nlp = None
        except Exception as e:
            logger.warning(f"spaCy failed to load (falling back to regex-only): {e}")
            _nlp = None
    return _nlp


def _run_nlp(text: str):
    """
    Safely run spaCy on text. Returns Doc or None if spaCy crashes
    (e.g. 'unable to infer type for attribute REGEX' on Python 3.14).
    """
    nlp = _get_nlp()
    if nlp is None:
        return None
    try:
        return nlp(text)
    except Exception as e:
        logger.warning(f"spaCy inference failed (using regex fallback): {e}")
        return None


# ── Regex patterns ─────────────────────────────────────────────────────────────

EMAIL_RE    = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE    = re.compile(
    r"(?:\+?[\d\-\(\)\s]{7,15})"
)
URL_RE      = re.compile(r"https?://[^\s]+|www\.[^\s]+")
LINKEDIN_RE = re.compile(r"linkedin\.com/in/[a-zA-Z0-9\-]+", re.IGNORECASE)
GITHUB_RE   = re.compile(r"github\.com/[a-zA-Z0-9\-]+", re.IGNORECASE)

# Section header patterns (order matters!)
SECTION_HEADERS = {
    "education":       re.compile(r"(?i)^\s*(education|academic|qualification|degree)s?\s*$"),
    "work_experience": re.compile(r"(?i)^\s*(work\s*experience|employment|experience|career\s*history|professional\s*experience)\s*$"),
    "skills":          re.compile(r"(?i)^\s*(skills?|technical\s*skills?|core\s*competenc|expertise)\s*$"),
    "certifications":  re.compile(r"(?i)^\s*(certif|licenses?|credentials?|accreditation)\s*$"),
    "projects":        re.compile(r"(?i)^\s*(projects?|portfolio|key\s*projects?)\s*$"),
    "summary":         re.compile(r"(?i)^\s*(summary|objective|profile|about\s*me|professional\s*summary)\s*$"),
    "contact":         re.compile(r"(?i)^\s*(contact|personal\s*information|personal\s*details)\s*$"),
    "references":      re.compile(r"(?i)^\s*(references?|referees?)\s*$"),
}


# ── Skills dictionary ──────────────────────────────────────────────────────────

def _load_skills_dict():
    """Import from config module."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config import SKILLS_KEYWORDS
        flat = set()
        for group in SKILLS_KEYWORDS.values():
            flat.update(k.lower() for k in group)
        return flat
    except Exception:
        return {
            "python", "java", "javascript", "sql", "html", "css",
            "react", "angular", "docker", "kubernetes", "aws", "git",
            "machine learning", "data analysis", "project management",
        }

SKILLS_DICT = _load_skills_dict()


# ── Main extraction function ───────────────────────────────────────────────────

def extract_profile(raw_text: str) -> dict:
    """
    Master function: takes raw resume text and returns a structured
    DEET profile dict with all fields populated.
    """
    text = _normalize_text(raw_text)
    sections = _split_sections(text)
    lines = text.splitlines()

    profile = {
        "full_name":       _extract_name(text, lines),
        "email":           _extract_email(text),
        "phone":           _extract_phone(text),
        "address":         _extract_address(text, sections),
        "linkedin":        _extract_linkedin(text),
        "github":          _extract_github(text),
        "summary":         _extract_summary(sections),
        "education":       _extract_education(sections.get("education", "")),
        "skills":          _extract_skills(sections.get("skills", "") + " " + text),
        "certifications":  _extract_certifications(sections.get("certifications", "")),
        "work_experience": _extract_experience(sections.get("work_experience", "")),
        "projects":        _extract_projects(sections.get("projects", "")),
        "raw_text":        raw_text,
    }
    return profile


# ── Text normalization ─────────────────────────────────────────────────────────

def _normalize_text(text: str) -> str:
    """Clean up common OCR artifacts and normalize whitespace."""
    # Fix common OCR substitutions
    text = re.sub(r"\|", "l", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)   # join single line-breaks
    text = re.sub(r"\n{3,}", "\n\n", text)           # collapse excess blank lines
    text = re.sub(r"[ \t]{2,}", " ", text)           # collapse spaces
    text = text.strip()
    return text


# ── Section splitting ──────────────────────────────────────────────────────────

def _split_sections(text: str) -> dict:
    """
    Split resume text into named sections using header patterns.
    Returns dict: { section_name: section_text }
    """
    sections = {}
    current_section = "header"
    current_lines = []

    for line in text.splitlines():
        matched = False
        for name, pattern in SECTION_HEADERS.items():
            if pattern.match(line):
                sections[current_section] = "\n".join(current_lines).strip()
                current_section = name
                current_lines = []
                matched = True
                break
        if not matched:
            current_lines.append(line)

    sections[current_section] = "\n".join(current_lines).strip()
    return sections


# ── Individual field extractors ────────────────────────────────────────────────

def _extract_name(text: str, lines: list) -> str:
    """
    Strategy: 1) spaCy PERSON entity in first 15 lines (if spaCy available)
              2) First non-empty line that looks like a name (regex fallback)
    """
    first_chunk = "\n".join(lines[:15])

    # Try spaCy NER — wrapped so any inference error is handled gracefully
    doc = _run_nlp(first_chunk)
    if doc is not None:
        for ent in doc.ents:
            if ent.label_ == "PERSON" and 2 <= len(ent.text.split()) <= 5:
                return ent.text.strip()

    # Fallback: first non-empty, non-email, non-phone, non-URL short line
    for line in lines[:8]:
        line = line.strip()
        if (line and len(line) > 3
                and not EMAIL_RE.search(line)
                and not PHONE_RE.search(line)
                and not URL_RE.search(line)
                and len(line.split()) <= 5
                and not any(c.isdigit() for c in line)):
            return line
    return ""


def _extract_email(text: str) -> str:
    match = EMAIL_RE.search(text)
    return match.group(0).strip() if match else ""


def _extract_phone(text: str) -> str:
    matches = PHONE_RE.findall(text)
    # Return the longest match that has enough digits
    for m in sorted(matches, key=len, reverse=True):
        digits = re.sub(r"\D", "", m)
        if 7 <= len(digits) <= 15:
            return m.strip()
    return ""


def _extract_linkedin(text: str) -> str:
    match = LINKEDIN_RE.search(text)
    return f"https://{match.group(0)}" if match else ""


def _extract_github(text: str) -> str:
    match = GITHUB_RE.search(text)
    return f"https://{match.group(0)}" if match else ""


def _extract_address(text: str, sections: dict) -> str:
    """Look for city/country patterns in contact header section."""
    header = sections.get("header", "") + "\n" + sections.get("contact", "")
    # Simple heuristic: look for comma-separated location tokens
    location_re = re.compile(
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)*,\s*[A-Z][a-z]+(?: [A-Z][a-z]+)*(?:,\s*[A-Z]{2,})?)"
    )
    match = location_re.search(header)
    if match:
        return match.group(0).strip()
    return ""


def _extract_summary(sections: dict) -> str:
    return sections.get("summary", "").strip()


def _extract_skills(text: str) -> list:
    """Match against skills dictionary. Case-insensitive."""
    text_lower = text.lower()
    found = []
    for skill in SKILLS_DICT:
        # Use word-boundary matching for short skills
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill.title())
    return sorted(set(found))


def _extract_education(text: str) -> list:
    """Extract education entries as list of dicts."""
    if not text.strip():
        return []

    entries = []
    # Split on year patterns or double-lines
    blocks = re.split(r"\n(?=\S)", text)
    degree_re   = re.compile(r"(?i)(bachelor|master|phd|doctorate|associate|diploma|certificate|b\.?sc|m\.?sc|m\.?a|b\.?a|b\.?eng|m\.?eng|mba)")
    year_re     = re.compile(r"\b(19|20)\d{2}\b")

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        entry = {
            "institution": "",
            "degree":      "",
            "field":       "",
            "year":        "",
            "raw":         block,
        }
        # Extract year
        years = year_re.findall(block)
        if years:
            entry["year"] = years[-1]

        # Extract degree
        deg_match = degree_re.search(block)
        if deg_match:
            entry["degree"] = deg_match.group(0).strip()

        # First long line is usually institution
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if lines:
            entry["institution"] = lines[0]

        entries.append(entry)

    return entries[:6]  # cap at 6 entries


def _extract_certifications(text: str) -> list:
    """Extract certifications as list of dicts."""
    if not text.strip():
        return []

    entries = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    year_re = re.compile(r"\b(19|20)\d{2}\b")

    for line in lines:
        if len(line) < 5:
            continue
        years = year_re.findall(line)
        entries.append({
            "name":   line,
            "issuer": "",
            "year":   years[-1] if years else "",
        })

    return entries[:10]


def _extract_experience(text: str) -> list:
    """Extract work experience entries."""
    if not text.strip():
        return []

    entries = []
    # Split on potential job blocks — blank lines or date patterns
    date_re = re.compile(
        r"(?i)(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}"
        r"|\d{4}\s*[-–—]\s*(?:\d{4}|present|current|now)"
    )
    year_re = re.compile(r"\b(19|20)\d{2}\b")

    blocks = re.split(r"\n{2,}", text)
    for block in blocks:
        block = block.strip()
        if not block or len(block) < 15:
            continue

        lines = [l.strip() for l in block.splitlines() if l.strip()]
        dates = date_re.findall(block)
        years = year_re.findall(block)

        entry = {
            "company":     "",
            "role":        "",
            "dates":       " | ".join([" ".join(d) if isinstance(d, tuple) else d for d in dates]) if dates else "",
            "description": block,
            "raw":         block,
        }

        if lines:
            # Heuristic: role is often title-case on first line, company on second
            entry["role"]    = lines[0]
            entry["company"] = lines[1] if len(lines) > 1 else ""

        entries.append(entry)

    return entries[:8]


def _extract_projects(text: str) -> list:
    """Extract project entries."""
    if not text.strip():
        return []

    entries = []
    blocks = re.split(r"\n{2,}", text)
    tech_re = re.compile(r"(?i)tech(?:nologies|nology|stack)?[:\-]\s*(.+)")

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 10:
            continue

        lines = [l.strip() for l in block.splitlines() if l.strip()]
        tech_match = tech_re.search(block)

        entry = {
            "name":        lines[0] if lines else "",
            "description": block,
            "technologies": tech_match.group(1).strip() if tech_match else "",
        }
        entries.append(entry)

    return entries[:6]
