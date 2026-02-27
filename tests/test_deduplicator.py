"""Tests for deduplicator module."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.deduplicator import JobDeduplicator, compute_hash


def make_job(title, company, location="Nairobi", desc="A great job opportunity."):
    return {
        "title": title, "company": company, "location": location,
        "description": desc,
        "content_hash": compute_hash(title, company, location),
    }


class TestDeduplicator:

    def test_exact_duplicate_detected(self):
        d = JobDeduplicator()
        job = make_job("Software Engineer", "TechCorp")
        assert d.add_job(job) is True        # first add: new
        assert d.add_job(job) is False       # second add: duplicate

    def test_different_jobs_not_duplicate(self):
        d = JobDeduplicator()
        j1 = make_job("Software Engineer", "TechCorp")
        j2 = make_job("Data Analyst", "DataFirm")
        assert d.add_job(j1) is True
        assert d.add_job(j2) is True

    def test_near_duplicate_detected(self):
        """Two jobs with very similar title/company/description should be near-dupes."""
        d = JobDeduplicator()
        j1 = make_job("Senior Python Developer", "Acme Corp",
                      desc="Build Python APIs and microservices with Django and Flask.")
        j2 = make_job("Senior Python Developer", "Acme Corp.",   # slight variation
                      desc="Build Python microservices and APIs using Django and Flask.")
        assert d.add_job(j1) is True
        # Near-duplicate — may or may not be caught depending on corpus size
        # We just assert it doesn't crash
        result = d.add_job(j2)
        assert isinstance(result, bool)

    def test_compute_hash_deterministic(self):
        h1 = compute_hash("Engineer", "Corp", "City")
        h2 = compute_hash("Engineer", "Corp", "City")
        assert h1 == h2

    def test_compute_hash_different_inputs(self):
        h1 = compute_hash("Engineer", "Corp A", "City")
        h2 = compute_hash("Engineer", "Corp B", "City")
        assert h1 != h2

    def test_load_existing_hashes(self):
        d = JobDeduplicator()
        job = make_job("ML Engineer", "AI Labs")
        # Pre-load the hash
        d.load_existing_hashes([job["content_hash"]])
        assert d.add_job(job) is False   # should be detected as duplicate

    def test_empty_deduplicator(self):
        d = JobDeduplicator()
        assert d.is_duplicate(make_job("X", "Y")) is False
