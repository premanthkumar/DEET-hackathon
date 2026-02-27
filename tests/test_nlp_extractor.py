"""Tests for NLP Extractor module."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.nlp_extractor import (
    extract_profile, _extract_email, _extract_phone,
    _extract_skills, _extract_linkedin, _split_sections,
    _normalize_text
)

SAMPLE_RESUME = """
John Doe
Software Engineer
john.doe@gmail.com | +1 (555) 987-6543 | linkedin.com/in/johndoe | github.com/johndoe
San Francisco, CA, USA

Summary
Experienced software engineer with 6 years of experience in building cloud-native applications.

Education
University of California, Berkeley
Bachelor of Science in Computer Science
2017

Skills
Python, JavaScript, React, Node.js, AWS, Docker, SQL, Machine Learning, Git

Work Experience
Senior Software Engineer
TechCorp Inc.
Jan 2020 – Present
Led development of microservices handling 5M daily requests. Reduced latency by 35%.

Software Engineer
StartupXYZ
June 2017 – December 2019
Built full-stack features with React and Django.

Certifications
AWS Certified Solutions Architect Associate — 2022
Google Professional Data Engineer — 2023

Projects
AI Resume Parser
Built NLP pipeline using spaCy to extract resume fields with 92% accuracy.
Technologies: Python, spaCy, Flask, React
"""


class TestNLPExtractor:

    def test_email_extraction(self):
        email = _extract_email(SAMPLE_RESUME)
        assert email == "john.doe@gmail.com", f"Expected email, got: {email}"

    def test_phone_extraction(self):
        phone = _extract_phone(SAMPLE_RESUME)
        digits = "".join(c for c in phone if c.isdigit())
        assert len(digits) >= 7, f"Phone digits insufficient: {phone}"

    def test_linkedin_extraction(self):
        from modules.nlp_extractor import _extract_linkedin
        linkedin = _extract_linkedin(SAMPLE_RESUME)
        assert "linkedin" in linkedin.lower(), f"LinkedIn not found: {linkedin}"

    def test_skills_extraction(self):
        skills = _extract_skills(SAMPLE_RESUME)
        assert len(skills) >= 3, f"Expected ≥3 skills, got: {skills}"
        # Check known skills are detected
        skills_lower = [s.lower() for s in skills]
        assert any("python" in s for s in skills_lower), "Python should be detected"

    def test_section_splitting(self):
        text = _normalize_text(SAMPLE_RESUME)
        sections = _split_sections(text)
        # Should detect at least some key sections
        section_keys = list(sections.keys())
        assert len(section_keys) >= 2, f"Expected multiple sections, got: {section_keys}"

    def test_full_profile_extraction(self):
        profile = extract_profile(SAMPLE_RESUME)

        assert isinstance(profile, dict), "Profile should be a dict"
        assert "full_name" in profile
        assert "email" in profile
        assert "skills" in profile
        assert "education" in profile
        assert "work_experience" in profile
        assert "projects" in profile

        # Email should be correct
        assert profile["email"] == "john.doe@gmail.com"

        # Skills should be a list
        assert isinstance(profile["skills"], list)

        # Education should be a list
        assert isinstance(profile["education"], list)

    def test_profile_has_raw_text(self):
        profile = extract_profile(SAMPLE_RESUME)
        assert "raw_text" in profile
        assert len(profile["raw_text"]) > 10

    def test_empty_text_graceful(self):
        """Should not crash on empty input."""
        profile = extract_profile("")
        assert isinstance(profile, dict)
        assert profile.get("email", "") == ""
        assert profile.get("skills", []) == []
