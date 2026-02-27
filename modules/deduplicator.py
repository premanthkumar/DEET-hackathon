"""
Deduplicator — detects duplicate and near-duplicate job postings.

Methods:
  1. Exact: SHA-256 hash of (title + company + location) [handled at DB level]
  2. Near-duplicate: Cosine similarity of TF-IDF vectors
"""

import re
import hashlib
import logging

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

COSINE_THRESHOLD = 0.85


class JobDeduplicator:
    """
    Maintains an in-memory TF-IDF index of seen jobs.
    Call add_job() for each new job; it returns False if duplicate.
    """

    def __init__(self, threshold: float = COSINE_THRESHOLD):
        self.threshold  = threshold
        self.corpus     = []       # list of text strings
        self.hashes     = set()    # exact hashes
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=5000,
            stop_words="english",
        )
        self._matrix    = None     # TF-IDF matrix (updated lazily)
        self._dirty     = False

    def is_duplicate(self, job: dict) -> bool:
        """
        Returns True if the job is a duplicate (exact OR near-duplicate).
        """
        h = job.get("content_hash") or _compute_hash(
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
        )

        # 1. Exact hash check
        if h in self.hashes:
            return True

        # 2. Near-duplicate: cosine similarity
        if len(self.corpus) >= 2:
            text = _job_to_text(job)
            try:
                query_vec = self.vectorizer.transform([text])
                if self._dirty or self._matrix is None:
                    self._rebuild_matrix()
                sims = cosine_similarity(query_vec, self._matrix).flatten()
                if sims.max() >= self.threshold:
                    logger.debug(f"Near-duplicate detected (sim={sims.max():.2f}): {job.get('title')}")
                    return True
            except Exception as e:
                logger.warning(f"Cosine similarity check failed: {e}")

        return False

    def add_job(self, job: dict) -> bool:
        """
        Add job to index. Returns True if added (new), False if duplicate.
        """
        if self.is_duplicate(job):
            return False

        h = job.get("content_hash") or _compute_hash(
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
        )
        self.hashes.add(h)
        self.corpus.append(_job_to_text(job))
        self._dirty = True

        # Refit vectorizer every 20 additions
        if len(self.corpus) % 20 == 0:
            self._rebuild_matrix()

        return True

    def _rebuild_matrix(self):
        if len(self.corpus) < 2:
            return
        self._matrix = self.vectorizer.fit_transform(self.corpus)
        self._dirty  = False

    def load_existing_hashes(self, hashes: list):
        """Preload hashes from database on startup."""
        self.hashes.update(hashes)

    def load_existing_jobs(self, jobs: list):
        """Preload existing job texts for near-dup detection."""
        for job in jobs:
            self.corpus.append(_job_to_text(job))
        if len(self.corpus) >= 2:
            self._rebuild_matrix()


def _job_to_text(job: dict) -> str:
    """Combine job fields into a single text string for vectorization."""
    parts = [
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
        job.get("description", "")[:500],
    ]
    return " ".join(p for p in parts if p).lower()


def _compute_hash(title: str, company: str, location: str) -> str:
    raw = f"{title.lower().strip()}|{company.lower().strip()}|{location.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def compute_hash(title: str, company: str, location: str) -> str:
    """Public alias."""
    return _compute_hash(title, company, location)
