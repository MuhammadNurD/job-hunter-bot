from __future__ import annotations

import re
from urllib.parse import urlparse

from ddgs import DDGS

from src.jobs.allan_gray import JobListing


EXCLUDED_DOMAINS = {
    "youtube.com",
    "youtu.be",
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "linkedin.com",
    "wikipedia.org",
}


def search_web_for_jobs(queries: list[str], max_results_per_query: int = 8) -> list[JobListing]:
    jobs: list[JobListing] = []
    seen_urls: set[str] = set()

    with DDGS() as ddgs:
        for query in queries:
            try:
                results = ddgs.text(query, max_results=max_results_per_query)
            except Exception:
                continue

            for result in results:
                url = result.get("href") or result.get("link") or ""
                if not url or url in seen_urls or not _is_job_url(url):
                    continue

                title = result.get("title") or "Job listing"
                body = result.get("body") or ""
                company = _infer_company(url, title, body)
                if "allan gray" not in f"{company} {title} {body} {url}".lower():
                    continue

                seen_urls.add(url)
                jobs.append(
                    JobListing(
                        title=_clean_title(title),
                        company=company,
                        description=body,
                        apply_url=url,
                        source="web_search",
                    )
                )

    return jobs


def _is_job_url(url: str) -> bool:
    host = urlparse(url).netloc.lower().replace("www.", "")
    if any(domain in host for domain in EXCLUDED_DOMAINS):
        return False
    path = urlparse(url).path.lower()
    job_signals = (
        "career",
        "job",
        "vacanc",
        "successfactors",
        "developer",
        "graduate",
    )
    return any(signal in f"{host}{path}" for signal in job_signals)


def _infer_company(url: str, title: str, body: str) -> str:
    host = urlparse(url).netloc.lower()
    if "allangray" in host:
        return "Allan Gray"
    if "successfactors" in host:
        return "Allan Gray"
    blob = f"{title} {body}".lower()
    if "allan gray" in blob:
        return "Allan Gray"
    return "Unknown"


def _clean_title(title: str) -> str:
    title = re.sub(r"\s*[\-|–|—]\s*Allan Gray.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*[\-|–|—]\s*LinkedIn.*$", "", title, flags=re.IGNORECASE)
    return title.strip()
