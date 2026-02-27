"""Tests for confidence scorer module."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.confidence_scorer import score_profile, get_confidence_label


class TestConfidenceScorer:

    def _make_profile(self, **kwargs):
        base = {
            "full_name": "", "email": "", "phone": "", "address": "",
            "linkedin": "", "github": "", "summary": "",
            "education": [], "skills": [], "certifications": [],
            "work_experience": [], "projects": [],
        }
        base.update(kwargs)
        return base

    def test_valid_email_scores_1(self):
        p = self._make_profile(email="user@example.com")
        scores = score_profile(p)
        assert scores["email"] == 1.0

    def test_invalid_email_scores_low(self):
        p = self._make_profile(email="notanemail")
        scores = score_profile(p)
        assert scores["email"] < 0.5

    def test_empty_field_scores_zero(self):
        p = self._make_profile()
        scores = score_profile(p)
        assert scores["email"]     == 0.0
        assert scores["full_name"] == 0.0
        assert scores["phone"]     == 0.0

    def test_valid_phone_scores_high(self):
        p = self._make_profile(phone="+1 555 123 4567")
        scores = score_profile(p)
        assert scores["phone"] >= 0.7

    def test_skills_list_scores(self):
        p = self._make_profile(skills=["Python", "SQL", "React", "AWS", "Docker"])
        scores = score_profile(p)
        assert scores["skills"] >= 0.7

    def test_well_formed_name_scores_high(self):
        p = self._make_profile(full_name="John Smith")
        scores = score_profile(p)
        assert scores["full_name"] >= 0.7

    def test_overall_score_in_range(self):
        p = self._make_profile(
            full_name="Alice Lee", email="alice@test.com",
            phone="+1555123456", skills=["Python", "SQL", "AWS"]
        )
        scores = score_profile(p)
        assert 0.0 <= scores["overall"] <= 1.0

    def test_confidence_labels(self):
        assert get_confidence_label(0.9)  == "high"
        assert get_confidence_label(0.65) == "medium"
        assert get_confidence_label(0.3)  == "low"
        assert get_confidence_label(0.0)  == "missing"
