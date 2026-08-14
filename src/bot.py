from __future__ import annotations

import time
from pathlib import Path

from src.alerts.notifier import send_alerts
from src.config import Config, load_config
from src.cv.advisor import build_cv_advice
from src.jobs.allan_gray import JobListing, filter_developer_jobs, scrape_allan_gray_careers
from src.jobs.web_search import search_web_for_jobs
from src.matching.matcher import MatchResult, rank_jobs
from src.profile.linkedin_parser import load_profile
from src.profile.schema import Profile
from src.storage.database import JobDatabase


def collect_jobs(config: Config) -> list[JobListing]:
    jobs: list[JobListing] = []
    jobs.extend(scrape_allan_gray_careers(config.search.allan_gray_careers_url))

    if config.search.web_search_enabled:
        jobs.extend(search_web_for_jobs(config.search.web_search_queries))

    deduped: dict[str, JobListing] = {}
    for job in jobs:
        deduped[job.stable_id()] = job
    unique_jobs = list(deduped.values())
    return filter_developer_jobs(unique_jobs, config.search.developer_keywords)


def run_scan(
    config: Config,
    profile: Profile,
    alert_new_only: bool = True,
) -> tuple[list[MatchResult], dict[str, object]]:
    db = JobDatabase(config.database_path)
    jobs = collect_jobs(config)
    matches = rank_jobs(profile, jobs, config.search.min_match_score)

    new_matches: list[MatchResult] = []
    advice_map = {}

    for match in matches:
        is_new = db.upsert_job(match.job)
        advice = build_cv_advice(profile, match, config)
        advice_map[match.job.stable_id()] = advice

        if alert_new_only and not is_new:
            continue
        new_matches.append(match)

    if new_matches:
        send_alerts(config.alerts, new_matches, advice_map)
        for match in new_matches:
            db.mark_alerted(match.job.stable_id())

    summary = {
        "jobs_found": len(jobs),
        "matches": len(matches),
        "new_alerts": len(new_matches),
    }
    return matches, summary


def watch(config: Config, profile: Profile) -> None:
    interval_seconds = max(3600, int(config.search.poll_interval_hours * 3600))
    print(f"Watching for new Allan Gray developer roles every {interval_seconds // 3600}h...")
    while True:
        _, summary = run_scan(config, profile, alert_new_only=True)
        print(f"Scan complete: {summary}")
        time.sleep(interval_seconds)


def ensure_profile(config: Config, pdf: Path | None, text: Path | None) -> Profile:
    return load_profile(config.profile_path, pdf_path=pdf, text_path=text)
