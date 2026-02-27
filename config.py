"""
Configuration constants for Resume-to-DEET system.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATABASE_PATH = os.path.join(BASE_DIR, "deet.db")

# Allowed file types for resume upload
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "png", "jpg", "jpeg"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

# OCR Settings
TESSERACT_DPI = 300
TESSERACT_LANG = "eng"

# NLP confidence thresholds
CONFIDENCE = {
    "regex_validated": 1.0,
    "ner_high": 0.88,
    "ner_medium": 0.72,
    "section_heuristic": 0.45,
    "missing": 0.0,
}

# Deduplication
DEDUP_COSINE_THRESHOLD = 0.85

# Employer verification
MIN_DOMAIN_AGE_DAYS = 180
EMPLOYER_TRUST_THRESHOLD = 0.6

# Scheduler
CRAWL_INTERVAL_HOURS = 6

# Target career pages to scrape (expandable list)
TARGET_CAREER_PAGES = [
    {
        "company": "Example Corp",
        "url": "https://example.com/careers",
        "job_selector": ".job-listing",
        "title_selector": ".job-title",
        "location_selector": ".job-location",
        "link_selector": "a",
    },
]

# DEET Job Categories
JOB_CATEGORIES = [
    "Information Technology",
    "Engineering",
    "Healthcare",
    "Education",
    "Finance & Accounting",
    "Marketing & Communications",
    "Administration",
    "Construction & Trades",
    "Agriculture",
    "Other",
]

# Skills dictionary (expandable)
SKILLS_KEYWORDS = {
    "programming": [
        "python", "java", "javascript", "typescript", "c++", "c#", "php",
        "ruby", "go", "swift", "kotlin", "r", "scala", "matlab",
    ],
    "web": [
        "html", "css", "react", "angular", "vue", "node.js", "django",
        "flask", "fastapi", "spring", "laravel", "express",
    ],
    "data": [
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "pandas", "numpy", "tensorflow", "pytorch", "scikit-learn",
        "power bi", "tableau", "excel", "data analysis", "machine learning",
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "git",
        "linux", "bash", "terraform", "ansible",
    ],
    "soft": [
        "leadership", "communication", "project management", "teamwork",
        "problem solving", "critical thinking", "time management",
    ],
}
