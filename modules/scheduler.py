"""
Scheduler — runs automated job crawl jobs on a configurable interval.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_scheduler = None


def start_scheduler(app=None):
    """Initialize and start the APScheduler background scheduler."""
    global _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger

        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config import CRAWL_INTERVAL_HOURS

        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.add_job(
            func=_run_crawl_job,
            trigger=IntervalTrigger(hours=CRAWL_INTERVAL_HOURS),
            id="job_crawl",
            name="Automated Job Crawl",
            replace_existing=True,
        )
        _scheduler.start()
        logger.info(f"Scheduler started — crawl every {CRAWL_INTERVAL_HOURS}h")
    except ImportError:
        logger.warning("APScheduler not installed. Scheduled crawls disabled.")
    except Exception as e:
        logger.error(f"Scheduler start failed: {e}")


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")


def _run_crawl_job():
    """The actual crawl function executed by the scheduler."""
    logger.info(f"[Scheduler] Starting crawl at {datetime.utcnow().isoformat()}")
    try:
        from pathlib import Path
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config      import TARGET_CAREER_PAGES
        from modules.job_scraper      import scrape_career_page
        from modules.job_classifier   import classify_batch
        from modules.deduplicator     import JobDeduplicator
        from modules.employer_verifier import verify_employer
        import database as db

        deduper = JobDeduplicator()
        # Preload existing hashes from DB
        existing, _ = db.get_jobs(page=1, per_page=10000)
        deduper.load_existing_jobs(existing)

        total_found = 0
        total_added = 0

        for target in TARGET_CAREER_PAGES:
            raw_jobs = scrape_career_page(target)
            total_found += len(raw_jobs)

            classify_batch(raw_jobs)

            for job in raw_jobs:
                # Employer verification (cached per domain)
                verification = verify_employer(job.get("source_url", ""))
                job["employer_score"] = verification["score"]
                job["is_verified"]    = verification["is_trusted"]

                if deduper.add_job(job):
                    saved = db.save_job(job)
                    if saved:
                        total_added += 1

            db.log_crawl(
                source_url=target.get("url", ""),
                jobs_found=len(raw_jobs),
                jobs_added=total_added,
                status="success",
            )

        logger.info(f"[Scheduler] Crawl done. Found={total_found}, Added={total_added}")
        return {"found": total_found, "added": total_added}
    except Exception as e:
        logger.error(f"[Scheduler] Crawl failed: {e}")
        return {"found": 0, "added": 0, "error": str(e)}


def trigger_manual_crawl() -> dict:
    """Trigger a crawl immediately (called from API endpoint)."""
    return _run_crawl_job()
