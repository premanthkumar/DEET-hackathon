"""Tests for the Flask API endpoints."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.fixture
def app():
    import database as db
    db.init_db()
    from app import app as flask_app
    flask_app.config["TESTING"] = True
    flask_app.config["UPLOAD_FOLDER"] = "/tmp/deet_test_uploads"
    import os
    os.makedirs("/tmp/deet_test_uploads", exist_ok=True)
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


class TestHealthEndpoint:
    def test_health_ok(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data["status"] == "ok"


class TestResumeAPI:

    def test_upload_no_file(self, client):
        res = client.post("/api/resume/upload")
        assert res.status_code == 400
        data = json.loads(res.data)
        assert "error" in data

    def test_upload_wrong_extension(self, client):
        data = {"resume": (b"fake content", "test.txt")}
        res = client.post("/api/resume/upload",
                          data=data, content_type="multipart/form-data")
        assert res.status_code == 415

    def test_submit_valid_profile(self, client):
        profile = {
            "full_name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "+1-555-1234",
            "skills": ["Python", "SQL"],
            "education": [],
            "work_experience": [],
        }
        res = client.post("/api/resume/submit",
                          data=json.dumps(profile),
                          content_type="application/json")
        assert res.status_code == 201
        data = json.loads(res.data)
        assert data["success"] is True
        assert "profile_id" in data

    def test_submit_missing_required(self, client):
        profile = {"full_name": "No Email"}
        res = client.post("/api/resume/submit",
                          data=json.dumps(profile),
                          content_type="application/json")
        assert res.status_code == 422

    def test_list_profiles(self, client):
        res = client.get("/api/resume/profiles")
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data["success"] is True
        assert isinstance(data["profiles"], list)


class TestJobsAPI:

    def test_list_jobs_empty(self, client):
        res = client.get("/api/jobs/list")
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data["success"] is True
        assert "jobs" in data

    def test_add_job_valid(self, client):
        job = {
            "title":   "Backend Developer",
            "company": "Test Corp",
            "location": "Remote",
            "experience_level": "Mid Level",
            "description": "Build REST APIs with Python and Flask.",
        }
        res = client.post("/api/jobs/add",
                          data=json.dumps(job),
                          content_type="application/json")
        assert res.status_code in (201, 409)  # 409 = duplicate OK in repeated runs

    def test_add_job_missing_fields(self, client):
        res = client.post("/api/jobs/add",
                          data=json.dumps({"title": "Only Title"}),
                          content_type="application/json")
        assert res.status_code == 422

    def test_add_duplicate_job(self, client):
        job = {"title": "DupJob", "company": "DupCo", "location": "DupCity"}
        client.post("/api/jobs/add", data=json.dumps(job), content_type="application/json")
        res = client.post("/api/jobs/add", data=json.dumps(job), content_type="application/json")
        assert res.status_code == 409

    def test_list_jobs_with_filter(self, client):
        # Add a categorized job first
        job = {
            "title": "Python Developer",
            "company": "FilterTest Inc",
            "description": "Python developer role",
        }
        client.post("/api/jobs/add", data=json.dumps(job), content_type="application/json")

        res = client.get("/api/jobs/list?category=Information+Technology")
        assert res.status_code == 200


class TestDashboardAPI:
    def test_stats_endpoint(self, client):
        res = client.get("/api/dashboard/stats")
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data["success"] is True
        assert "total_jobs" in data["stats"]
