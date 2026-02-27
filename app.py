"""
Flask API entry point — Resume-to-DEET Instant Registration System.
"""

import os
import json
import logging
import tempfile
from pathlib import Path

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

import config
import database as db
from modules.ocr_engine        import extract_text
from modules.nlp_extractor     import extract_profile
from modules.confidence_scorer import score_profile, get_confidence_label
from modules.job_classifier    import classify_job
from modules.deduplicator      import JobDeduplicator
from modules.employer_verifier import verify_employer
from modules.scheduler         import start_scheduler, trigger_manual_crawl

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── App factory ────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config["UPLOAD_FOLDER"]     = config.UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
CORS(app)

# Ensure directories exist
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs("models", exist_ok=True)

# Global deduplicator (loaded at startup)
_deduper = JobDeduplicator()


def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )


# ── Template routes ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/jobs")
def jobs_page():
    return render_template("jobs.html")


@app.route("/preview")
def preview_page():
    return render_template("preview.html")


# ── Resume API ─────────────────────────────────────────────────────────────────

@app.route("/api/resume/upload", methods=["POST"])
def upload_resume():
    """
    POST /api/resume/upload
    Accepts: multipart/form-data with field 'resume'
    Returns: JSON with extracted profile + confidence scores
    """
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded. Use field name 'resume'."}), 400

    file = request.files["resume"]
    if not file or file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    if not _allowed_file(file.filename):
        return jsonify({
            "error": f"Unsupported file type. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"
        }), 415

    # Save temporarily
    filename = secure_filename(file.filename)
    tmp_path = os.path.join(config.UPLOAD_FOLDER, filename)
    file.save(tmp_path)

    try:
        # Stage 1: OCR / text extraction
        ocr_result = extract_text(tmp_path)
        raw_text   = ocr_result.get("raw_text", "")

        if not raw_text.strip():
            return jsonify({"error": "Could not extract text from the uploaded file."}), 422

        # Stage 2: NLP extraction
        profile = extract_profile(raw_text)

        # Stage 3: Confidence scoring
        scores  = score_profile(profile)
        profile["confidence_scores"] = scores

        # Annotate each field with confidence label for UI
        confidence_labels = {
            field: get_confidence_label(score)
            for field, score in scores.items()
        }
        profile["confidence_labels"] = confidence_labels
        profile["ocr_method"]        = ocr_result.get("method", "unknown")
        profile["ocr_used"]          = ocr_result.get("ocr_used", False)

        return jsonify({"success": True, "profile": profile}), 200

    except Exception as e:
        logger.error(f"Resume processing failed: {e}", exc_info=True)
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500
    finally:
        # Clean up uploaded file
        try:
            os.remove(tmp_path)
        except Exception:
            pass


@app.route("/api/resume/submit", methods=["POST"])
def submit_profile():
    """
    POST /api/resume/submit
    Body: JSON profile (possibly user-edited)
    Returns: { "success": true, "profile_id": int }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body provided."}), 400

    required = ["full_name", "email"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Required field missing: {field}"}), 422

    try:
        profile_id = db.save_profile(data)
        return jsonify({"success": True, "profile_id": profile_id}), 201
    except Exception as e:
        logger.error(f"Profile save failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/resume/profiles", methods=["GET"])
def list_profiles():
    """GET /api/resume/profiles — list all saved profiles."""
    try:
        profiles = db.get_all_profiles()
        return jsonify({"success": True, "profiles": profiles, "total": len(profiles)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Jobs API ───────────────────────────────────────────────────────────────────

@app.route("/api/jobs/list", methods=["GET"])
def list_jobs():
    """
    GET /api/jobs/list?page=1&per_page=20&category=IT&location=...&search=...
    """
    try:
        page     = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        category = request.args.get("category")
        location = request.args.get("location")
        search   = request.args.get("search")

        jobs, total = db.get_jobs(
            page=page, per_page=per_page,
            category=category, location=location, search=search
        )

        # Parse JSON fields stored as strings
        for job in jobs:
            for field in ["skills_required"]:
                if isinstance(job.get(field), str):
                    try:
                        job[field] = json.loads(job[field])
                    except Exception:
                        job[field] = []

        return jsonify({
            "success":  True,
            "jobs":     jobs,
            "total":    total,
            "page":     page,
            "per_page": per_page,
            "pages":    (total + per_page - 1) // per_page,
        }), 200
    except Exception as e:
        logger.error(f"Job list failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jobs/crawl", methods=["POST"])
def crawl_jobs():
    """POST /api/jobs/crawl — trigger a manual job crawl."""
    try:
        result = trigger_manual_crawl()
        return jsonify({"success": True, "result": result}), 200
    except Exception as e:
        logger.error(f"Manual crawl failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jobs/add", methods=["POST"])
def add_job_manually():
    """
    POST /api/jobs/add — manually add a job posting (admin/employer submission).
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body."}), 400

    required = ["title", "company"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Required field missing: {field}"}), 422

    try:
        from modules.deduplicator import compute_hash
        data["content_hash"] = compute_hash(
            data.get("title", ""),
            data.get("company", ""),
            data.get("location", ""),
        )
        data["category"] = classify_job(data)

        if data.get("source_url") or data.get("application_link"):
            url = data.get("source_url") or data.get("application_link", "")
            verification = verify_employer(url)
            data["employer_score"] = verification["score"]
            data["is_verified"]    = verification["is_trusted"]

        saved = db.save_job(data)
        if saved:
            return jsonify({"success": True, "message": "Job added."}), 201
        else:
            return jsonify({"success": False, "message": "Duplicate job detected."}), 409
    except Exception as e:
        logger.error(f"Manual job add failed: {e}")
        return jsonify({"error": str(e)}), 500


# ── Dashboard / Stats API ──────────────────────────────────────────────────────

@app.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    """GET /api/dashboard/stats — summary statistics."""
    try:
        stats = db.get_job_stats()
        return jsonify({"success": True, "stats": stats}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Health check ───────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Resume-to-DEET API",
        "version": "1.0.0",
    }), 200


# ── Bootstrap ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db.init_db()
    # Preload existing job hashes into deduplicator
    existing_jobs, _ = db.get_jobs(page=1, per_page=5000)
    _deduper.load_existing_jobs(existing_jobs)

    # Start background scheduler
    start_scheduler(app)

    logger.info("Starting Resume-to-DEET server on http://localhost:5000")
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5000)
