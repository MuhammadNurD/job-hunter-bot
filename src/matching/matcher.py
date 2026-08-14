from __future__ import annotations

from dataclasses import dataclass, field

import re

from src.jobs.allan_gray import JobListing
from src.profile.schema import Profile


TECH_KEYWORDS = {
    "python": ["python", "django", "flask", "fastapi"],
    "javascript": ["javascript", "typescript", "node", "nodejs", "react", "angular", "vue"],
    "java": ["java", "spring", "kotlin"],
    "csharp": ["c#", ".net", "dotnet", "asp.net"],
    "cloud": ["aws", "azure", "gcp", "cloud", "kubernetes", "k8s", "docker", "container"],
    "data": ["sql", "postgres", "mysql", "database", "data engineer", "etl"],
    "devops": ["devops", "ci/cd", "terraform", "ansible", "jenkins", "github actions"],
    "testing": ["test", "qa", "selenium", "cypress", "jest"],
    "architecture": ["microservices", "api", "rest", "graphql", "system design"],
    "finance": ["financial", "investment", "asset management", "fintech"],
}


@dataclass
class MatchResult:
    job: JobListing
    score: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    rationale: str = ""


def _tokens(text: str) -> set[str]:
    cleaned = re.sub(r"\([^)]*\)", " ", text)
    return {
        token.strip().lower()
        for token in cleaned.replace("/", " ").split()
        if len(token.strip()) > 2 and token.strip().isalpha()
    }


def _profile_keywords(profile: Profile) -> set[str]:
    keywords = set(profile.skill_set())
    keywords.update(_tokens(profile.all_text()))
    for group_terms in TECH_KEYWORDS.values():
        blob = profile.all_text()
        if any(term in blob for term in group_terms):
            keywords.update(group_terms)
    return keywords


def _job_keywords(job: JobListing) -> set[str]:
    blob = f"{job.title} {job.description} {job.company}".lower()
    keywords: set[str] = set()
    for group, terms in TECH_KEYWORDS.items():
        if any(term in blob for term in terms):
            keywords.add(group)
            keywords.update(terms)
    keywords.update(_tokens(blob))
    return keywords


def match_job(profile: Profile, job: JobListing) -> MatchResult:
    profile_kw = _profile_keywords(profile)
    job_kw = _job_keywords(job)
    overlap = profile_kw & job_kw

    title_blob = job.title.lower()
    seniority_bonus = 0.0
    for exp in profile.experience:
        if any(word in title_blob for word in _tokens(exp.title)):
            seniority_bonus += 0.15

    role_bonus = 0.0
    if any(term in title_blob for term in ("developer", "engineer", "software", "devops")):
        if any(term in profile.all_text() for term in ("developer", "engineer", "software")):
            role_bonus += 0.25

    if not job_kw:
        score = 0.2 + seniority_bonus + role_bonus
    else:
        score = len(overlap) / max(len(job_kw), 1)
        score = min(1.0, score + seniority_bonus + role_bonus)

    matched = sorted(skill for skill in profile.skills if skill.lower() in job.description.lower())
    missing = sorted(
        term
        for term in job_kw
        if term not in profile_kw and len(term) > 2 and not term.isdigit()
    )[:8]

    rationale_parts = []
    if matched:
        rationale_parts.append(f"Your profile mentions {', '.join(matched[:5])}.")
    if missing:
        rationale_parts.append(f"Role highlights {', '.join(missing[:5])}.")
    if seniority_bonus:
        rationale_parts.append("Your past job titles align with this role.")

    return MatchResult(
        job=job,
        score=round(min(score, 1.0), 3),
        matched_skills=matched,
        missing_skills=missing,
        rationale=" ".join(rationale_parts) or "General developer profile fit.",
    )


def rank_jobs(profile: Profile, jobs: list[JobListing], min_score: float) -> list[MatchResult]:
    results = [match_job(profile, job) for job in jobs]
    results.sort(key=lambda item: item.score, reverse=True)
    return [item for item in results if item.score >= min_score]
