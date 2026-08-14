from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import hashlib
import re
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class JobListing:
    title: str
    company: str
    location: str = ""
    closing_date: str = ""
    description: str = ""
    apply_url: str = ""
    source: str = ""
    job_id: str = ""
    discovered_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def stable_id(self) -> str:
        if self.job_id:
            return self.job_id
        key = f"{self.company}|{self.title}|{self.apply_url}".lower()
        return hashlib.sha256(key.encode()).hexdigest()[:16]


USER_AGENT = (
    "Mozilla/5.0 (compatible; JobHunterBot/1.0; +https://github.com/job-hunter-bot)"
)


def _get(url: str, timeout: int = 30) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en-GB,en;q=0.9"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


def _extract_job_req_id(url: str) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    req_ids = params.get("career_job_req_id") or params.get("jobReqId")
    return req_ids[0] if req_ids else ""


def _fetch_job_description(apply_url: str) -> str:
    if not apply_url or "successfactors" not in apply_url:
        return ""
    try:
        html = _get(apply_url)
        soup = BeautifulSoup(html, "html.parser")
        for selector in ("#jobAppPageDesc", ".jobdescription", "[data-automation-id='jobPostingDescription']"):
            node = soup.select_one(selector)
            if node:
                return node.get_text(" ", strip=True)
        return soup.get_text(" ", strip=True)[:4000]
    except requests.RequestException:
        return ""


def scrape_allan_gray_careers(careers_url: str) -> list[JobListing]:
    html = _get(careers_url)
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[JobListing] = []
    seen: set[str] = set()

    carousel = soup.select_one("#careers-vacancies")
    if not carousel:
        return jobs

    for item in carousel.select(".carousel__item"):
        title_node = item.select_one(".carousel__title h4, .carousel__title h3, h4, h3")
        link = item.find("a", href=True, attrs={"data-qatag": True}) or item.find(
            "a", href=lambda href: href and "career_job_req_id" in href
        )
        if not title_node or not link:
            continue

        title = title_node.get_text(strip=True)
        apply_url = link["href"]
        if apply_url.startswith("/"):
            apply_url = f"https://www.allangray.co.za{apply_url}"

        job_id = _extract_job_req_id(apply_url) or JobListing(
            title=title, company="Allan Gray", apply_url=apply_url
        ).stable_id()
        if job_id in seen:
            continue
        seen.add(job_id)

        location = ""
        closing = ""
        for node in item.select(".carousel__details p, p"):
            text = node.get_text(" ", strip=True)
            if text.lower().startswith("location"):
                location = text.split(":", 1)[-1].strip()
            if "closing" in text.lower():
                closing = text.split(":", 1)[-1].strip()

        jobs.append(
            JobListing(
                title=title,
                company="Allan Gray",
                location=location or "Cape Town, South Africa",
                closing_date=closing,
                apply_url=apply_url,
                source="allan_gray_careers",
                job_id=job_id,
            )
        )

    if not jobs:
        for link in soup.select('a[href*="career_job_req_id"]'):
            title = link.get_text(strip=True) or "Allan Gray vacancy"
            apply_url = link["href"]
            job_id = _extract_job_req_id(apply_url)
            if job_id in seen:
                continue
            seen.add(job_id)
            jobs.append(
                JobListing(
                    title=title,
                    company="Allan Gray",
                    location="Cape Town, South Africa",
                    apply_url=apply_url,
                    source="allan_gray_careers",
                    job_id=job_id,
                )
            )

    for job in jobs:
        if not job.description:
            job.description = _fetch_job_description(job.apply_url)

    return jobs


def is_developer_role(title: str, description: str, keywords: list[str]) -> bool:
    blob = f"{title} {description}".lower()
    return any(keyword.lower() in blob for keyword in keywords)


def filter_developer_jobs(jobs: list[JobListing], keywords: list[str]) -> list[JobListing]:
    filtered: list[JobListing] = []
    for job in jobs:
        if is_developer_role(job.title, job.description, keywords):
            filtered.append(job)
            continue
        if job.source == "web_search" and "allan gray" in f"{job.company} {job.title} {job.description}".lower():
            if is_developer_role(job.title, job.description, keywords):
                filtered.append(job)
    return filtered
