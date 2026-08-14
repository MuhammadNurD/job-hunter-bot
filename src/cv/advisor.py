from __future__ import annotations

from dataclasses import dataclass, field
import json

import requests

from src.config import Config
from src.matching.matcher import MatchResult
from src.profile.schema import Profile


@dataclass
class CvAdvice:
    suggestions: list[str] = field(default_factory=list)
    summary_line: str = ""
    keywords_to_add: list[str] = field(default_factory=list)


def build_cv_advice(profile: Profile, match: MatchResult, config: Config) -> CvAdvice:
    if config.openai_api_key:
        ai_advice = _openai_advice(profile, match, config)
        if ai_advice:
            return ai_advice
    return _rule_based_advice(profile, match)


def _rule_based_advice(profile: Profile, match: MatchResult) -> CvAdvice:
    suggestions: list[str] = []
    job = match.job
    blob = f"{job.title} {job.description}".lower()

    if "microservices" in blob and "microservices" not in profile.all_text():
        suggestions.append("Add microservices experience to your skills or project bullets.")
    if ".net" in blob or "dotnet" in blob:
        if not any(".net" in skill.lower() or "c#" in skill.lower() for skill in profile.skills):
            suggestions.append("Highlight any C# or .NET experience, including coursework or side projects.")
    if "react" in blob and "react" not in profile.all_text():
        suggestions.append("Mention React projects explicitly in your experience section.")
    if "kubernetes" in blob or "docker" in blob:
        suggestions.append("Emphasize containerisation and cloud deployment work (Docker/Kubernetes).")
    if "financial" in blob or "investment" in blob:
        suggestions.append(
            "Tailor your summary to financial services: reliability, compliance awareness, and client impact."
        )
    if match.missing_skills:
        suggestions.append(
            f"Address these role keywords in your CV: {', '.join(match.missing_skills[:5])}."
        )
    if not suggestions:
        suggestions.append("Lead with outcomes and metrics in your most recent developer roles.")

    headline = profile.headline or "Software Developer"
    summary_line = (
        f"{headline} with strengths in {', '.join(match.matched_skills[:3]) or 'modern software delivery'}, "
        f"seeking a {job.title} role at Allan Gray."
    )

    return CvAdvice(
        suggestions=suggestions,
        summary_line=summary_line,
        keywords_to_add=match.missing_skills[:6],
    )


def _openai_advice(profile: Profile, match: MatchResult, config: Config) -> CvAdvice | None:
    prompt = {
        "profile": {
            "headline": profile.headline,
            "summary": profile.summary,
            "skills": profile.skills,
            "experience": [
                {"title": exp.title, "company": exp.company, "description": exp.description}
                for exp in profile.experience
            ],
        },
        "job": {
            "title": match.job.title,
            "description": match.job.description[:2500],
            "apply_url": match.job.apply_url,
        },
        "match": {
            "score": match.score,
            "matched_skills": match.matched_skills,
            "missing_skills": match.missing_skills,
        },
        "instructions": (
            "Return JSON with keys: suggestions (list of 3-5 CV edit tips), "
            "summary_line (one tailored professional summary sentence), "
            "keywords_to_add (list of strings)."
        ),
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.openai_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a career coach helping tailor CVs for developer roles.",
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.4,
            },
            timeout=45,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        return CvAdvice(
            suggestions=data.get("suggestions", []),
            summary_line=data.get("summary_line", ""),
            keywords_to_add=data.get("keywords_to_add", []),
        )
    except (requests.RequestException, KeyError, json.JSONDecodeError, IndexError):
        return None
