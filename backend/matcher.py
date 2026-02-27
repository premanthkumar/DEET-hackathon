from google import genai
import json
import os
import re
import time
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2


def _get_model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")
    return genai.Client(api_key=api_key)


def match_jobs(profile: dict, jobs: list[dict]) -> list[dict]:
    if not jobs:
        return []

    scores = batch_calculate_matches(profile, jobs)

    results = []
    for i, job in enumerate(jobs):
        score_data = scores[i] if i < len(scores) else {"score": 50, "reason": "Could not evaluate match"}
        results.append({
            **job,
            "match_score": score_data.get("score", 50),
            "match_reason": score_data.get("reason", "No reason provided"),
        })

    return sorted(results, key=lambda x: x["match_score"], reverse=True)


def batch_calculate_matches(profile: dict, jobs: list[dict]) -> list[dict]:
    jobs_text = "\n".join(
        f'{i}. Title: {job.get("title")} | Skills: {job.get("skills", [])}'
        for i, job in enumerate(jobs)
    )

    prompt = f"""
    Rate how well this candidate matches each job below.
    Return ONLY a valid JSON array — no explanation, no markdown, no code fences.

    Candidate:
    - Skills: {profile.get('skills', [])}
    - Experience: {profile.get('experience_years', 0)} years
    - Previous roles: {profile.get('previous_roles', [])}

    Jobs:
    {jobs_text}

    Return a JSON array with one object per job (in the same order), like:
    [
      {{"score": <0-100>, "reason": "<one sentence>"}},
      ...
    ]
    """

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client = _get_model()
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt
            )
            text = response.text.strip()
            text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
            parsed = json.loads(text)

            if isinstance(parsed, list) and len(parsed) == len(jobs):
                logger.info(f"[matcher] Batch scored {len(jobs)} jobs successfully")
                return parsed

            logger.warning(f"[matcher] Response length mismatch: expected {len(jobs)}, got {len(parsed)}")
            return _fallback_scores(len(jobs))

        except json.JSONDecodeError as e:
            logger.error(f"[matcher] JSON decode error on attempt {attempt}: {e}")
        except Exception as e:
            logger.error(f"[matcher] Gemini API error on attempt {attempt}: {e}")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY * attempt)

    logger.error("[matcher] All retry attempts failed, returning fallback scores")
    return _fallback_scores(len(jobs))


def _fallback_scores(count: int) -> list[dict]:
    return [
        {"score": 50, "reason": "Match could not be evaluated — AI service unavailable"}
        for _ in range(count)
    ]