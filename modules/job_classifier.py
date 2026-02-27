"""
Job Classifier — classifies job postings into DEET categories.

Primary:   scikit-learn TF-IDF + Logistic Regression (if model trained)
Fallback:  rule-based keyword matching (always works, no training needed)
"""

import re
import os
import pickle
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent.parent / "models" / "job_classifier.pkl"

CATEGORY_KEYWORDS = {
    "Information Technology": [
        "software", "developer", "engineer", "programmer", "python", "java",
        "javascript", "backend", "frontend", "fullstack", "devops", "cloud",
        "aws", "azure", "database", "sql", "api", "cybersecurity", "network",
        "system administrator", "it support", "data science", "machine learning",
        "artificial intelligence", "ios", "android", "mobile", "web developer",
    ],
    "Engineering": [
        "civil engineer", "mechanical engineer", "electrical engineer",
        "structural", "geotechnical", "construction", "autocad", "solidworks",
        "project engineer", "site engineer", "piping", "hvac", "surveyor",
        "quantity surveyor", "material engineer",
    ],
    "Healthcare": [
        "nurse", "doctor", "physician", "pharmacist", "medical", "clinical",
        "hospital", "healthcare", "patient", "surgery", "diagnosis", "lab",
        "radiologist", "dentist", "therapist", "midwife", "health officer",
        "public health", "nutrition",
    ],
    "Education": [
        "teacher", "lecturer", "professor", "tutor", "instructor",
        "curriculum", "school", "university", "college", "education",
        "training", "trainer", "e-learning", "academic", "pedagogy",
    ],
    "Finance & Accounting": [
        "accountant", "auditor", "finance", "financial analyst", "treasurer",
        "budget", "tax", "bookkeeper", "cpa", "cfa", "banking", "investment",
        "risk management", "compliance", "payroll",
    ],
    "Marketing & Communications": [
        "marketing", "brand", "social media", "content", "copywriter",
        "seo", "digital marketing", "public relations", "communications",
        "advertising", "campaign", "media", "journalist", "editor",
    ],
    "Administration": [
        "administrative", "office manager", "receptionist", "secretary",
        "executive assistant", "data entry", "records", "coordinator",
        "logistics", "operations", "procurement", "hr", "human resource",
        "recruitment",
    ],
    "Construction & Trades": [
        "carpenter", "electrician", "plumber", "welder", "mason",
        "construction worker", "foreman", "technician", "maintenance",
        "mechanic", "fitter", "rigger", "scaffolding",
    ],
    "Agriculture": [
        "agriculture", "farm", "agri", "crops", "livestock", "fisheries",
        "horticulture", "agronomist", "plantation", "forestry", "veterinary",
    ],
}


def classify_job(job: dict) -> str:
    """
    Classify a job into a DEET category.
    Returns category string.
    """
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()

    # Try ML model first
    ml_result = _ml_classify(text)
    if ml_result:
        return ml_result

    # Fallback: keyword scoring
    return _keyword_classify(text)


def classify_batch(jobs: list) -> list:
    """Classify a list of jobs in-place, returns the same list."""
    for job in jobs:
        job["category"] = classify_job(job)
    return jobs


def _keyword_classify(text: str) -> str:
    best_category = "Other"
    best_score    = 0

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score    = score
            best_category = category

    return best_category


def _ml_classify(text: str) -> str | None:
    """Try loading saved sklearn model. Returns None if unavailable."""
    if not MODEL_PATH.exists():
        return None
    try:
        with open(MODEL_PATH, "rb") as f:
            model_bundle = pickle.load(f)
        vectorizer  = model_bundle["vectorizer"]
        classifier  = model_bundle["classifier"]
        label_map   = model_bundle["labels"]
        X = vectorizer.transform([text])
        pred = classifier.predict(X)[0]
        return label_map.get(pred, "Other")
    except Exception as e:
        logger.warning(f"ML classifier failed: {e}")
        return None


def train_classifier(training_data: list[dict], save: bool = True):
    """
    Train the sklearn classifier from labeled data.

    Args:
        training_data: list of {"text": str, "category": str}
        save: persist model to disk
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model    import LogisticRegression
        from sklearn.pipeline        import Pipeline
        from sklearn.model_selection import train_test_split
        from sklearn.metrics         import classification_report

        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config import JOB_CATEGORIES

        labels    = {cat: i for i, cat in enumerate(JOB_CATEGORIES)}
        rev_labels = {v: k for k, v in labels.items()}

        texts  = [d["text"] for d in training_data]
        y      = [labels.get(d["category"], len(JOB_CATEGORIES) - 1) for d in training_data]

        X_train, X_test, y_train, y_test = train_test_split(
            texts, y, test_size=0.2, random_state=42
        )

        vectorizer  = TfidfVectorizer(ngram_range=(1, 2), max_features=10000, stop_words="english")
        classifier  = LogisticRegression(max_iter=1000, C=1.0)

        X_train_vec = vectorizer.fit_transform(X_train)
        classifier.fit(X_train_vec, y_train)

        X_test_vec  = vectorizer.transform(X_test)
        preds       = classifier.predict(X_test_vec)
        logger.info("\n" + classification_report(y_test, preds,
                    target_names=list(labels.keys()), zero_division=0))

        if save:
            MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(MODEL_PATH, "wb") as f:
                pickle.dump({
                    "vectorizer": vectorizer,
                    "classifier": classifier,
                    "labels":     rev_labels,
                }, f)
            logger.info(f"Model saved to {MODEL_PATH}")

        return classifier, vectorizer
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return None, None
