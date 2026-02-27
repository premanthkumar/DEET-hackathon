import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def match_jobs(profile: dict, jobs: List[dict]) -> List[dict]:
    """
    Match a candidate profile against a list of jobs using local heuristics only.
    Scores are based on skill overlap plus a small boost for experience.
    """
    if not jobs:
        return []

    scores = _calculate_matches(profile, jobs)

    results = []
    for i, job in enumerate(jobs):
        score_data = scores[i] if i < len(scores) else {"score": 0, "reason": "Could not evaluate match"}
        results.append(
            {
                **job,
                "match_score": int(score_data.get("score", 0)),
                "match_reason": score_data.get("reason", "No reason provided"),
            }
        )

    return sorted(results, key=lambda x: x["match_score"], reverse=True)


def _calculate_matches(profile: dict, jobs: List[dict]) -> List[Dict[str, object]]:
    """
    Simple scoring:
    - Jaccard-style similarity between profile.skills and job.skills.
    - +0 / +5 / +10 bonus depending on experience_years.
    """
    profile_skills = {s.lower() for s in profile.get("skills", []) if isinstance(s, str)}
    experience_years = profile.get("experience_years", 0) or 0

    results: List[Dict[str, object]] = []

    for job in jobs:
        job_skills = {s.lower() for s in job.get("skills", []) if isinstance(s, str)}

        if profile_skills or job_skills:
            overlap = profile_skills & job_skills
            union = profile_skills | job_skills or {""}
            base = len(overlap) / len(union)  # 0–1
        else:
            overlap = set()
            base = 0.0

        score = base * 100

        # Experience bonus
        if experience_years >= 5:
            score += 10
        elif experience_years >= 2:
            score += 5

        score = max(0, min(100, round(score)))

        if overlap:
            reason = f"Matched on skills: {', '.join(sorted({s.title() for s in overlap}))}"
        else:
            reason = "No overlapping skills found; based on limited profile information"

        results.append({"score": score, "reason": reason})

    logger.info(f"[matcher] Heuristically scored {len(jobs)} jobs")
    return results