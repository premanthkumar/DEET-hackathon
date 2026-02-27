"""
Database initialization and helper functions for Resume-to-DEET system.
"""

import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            education TEXT DEFAULT '[]',
            skills TEXT DEFAULT '[]',
            certifications TEXT DEFAULT '[]',
            work_experience TEXT DEFAULT '[]',
            projects TEXT DEFAULT '[]',
            confidence_scores TEXT DEFAULT '{}',
            raw_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            skills_required TEXT DEFAULT '[]',
            experience_level TEXT DEFAULT 'Not Specified',
            category TEXT DEFAULT 'Other',
            application_link TEXT,
            employer_score REAL DEFAULT 0.0,
            content_hash TEXT UNIQUE,
            source_url TEXT,
            is_verified INTEGER DEFAULT 0,
            description TEXT,
            discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawl_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT,
            jobs_found INTEGER DEFAULT 0,
            jobs_added INTEGER DEFAULT 0,
            status TEXT,
            crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ── Profile helpers ────────────────────────────────────────────────────────────

def save_profile(profile: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO profiles
        (full_name, email, phone, address, education, skills, certifications,
         work_experience, projects, confidence_scores, raw_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        profile.get("full_name", ""),
        profile.get("email", ""),
        profile.get("phone", ""),
        profile.get("address", ""),
        json.dumps(profile.get("education", [])),
        json.dumps(profile.get("skills", [])),
        json.dumps(profile.get("certifications", [])),
        json.dumps(profile.get("work_experience", [])),
        json.dumps(profile.get("projects", [])),
        json.dumps(profile.get("confidence_scores", {})),
        profile.get("raw_text", ""),
        datetime.utcnow().isoformat(),
    ))
    profile_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return profile_id


def get_all_profiles():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM profiles ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Job helpers ────────────────────────────────────────────────────────────────

def save_job(job: dict) -> bool:
    """Returns True if new, False if duplicate."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs
            (title, company, location, skills_required, experience_level,
             category, application_link, employer_score, content_hash,
             source_url, is_verified, description, discovered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
            json.dumps(job.get("skills_required", [])),
            job.get("experience_level", "Not Specified"),
            job.get("category", "Other"),
            job.get("application_link", ""),
            job.get("employer_score", 0.0),
            job.get("content_hash", ""),
            job.get("source_url", ""),
            1 if job.get("is_verified", False) else 0,
            job.get("description", ""),
            datetime.utcnow().isoformat(),
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate content_hash
        return False
    finally:
        conn.close()


def get_jobs(page: int = 1, per_page: int = 20, category: str = None,
             location: str = None, search: str = None):
    conn = get_connection()
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if search:
        query += " AND (title LIKE ? OR company LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY discovered_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    rows = conn.execute(query, params).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    conn.close()
    return [dict(r) for r in rows], total


def get_job_stats():
    conn = get_connection()
    stats = {
        "total_jobs": conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
        "verified_jobs": conn.execute("SELECT COUNT(*) FROM jobs WHERE is_verified=1").fetchone()[0],
        "total_profiles": conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0],
        "categories": {},
    }
    rows = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM jobs GROUP BY category"
    ).fetchall()
    for row in rows:
        stats["categories"][row["category"]] = row["cnt"]
    conn.close()
    return stats


def log_crawl(source_url: str, jobs_found: int, jobs_added: int, status: str):
    conn = get_connection()
    conn.execute("""
        INSERT INTO crawl_log (source_url, jobs_found, jobs_added, status, crawled_at)
        VALUES (?, ?, ?, ?, ?)
    """, (source_url, jobs_found, jobs_added, status, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
