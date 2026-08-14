from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader

from src.profile.schema import Experience, Profile


def load_profile_json(path: Path) -> Profile:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    experience = [
        Experience(
            title=item.get("title", ""),
            company=item.get("company", ""),
            duration=item.get("duration", ""),
            description=item.get("description", ""),
        )
        for item in data.get("experience", [])
    ]

    return Profile(
        name=data.get("name", ""),
        headline=data.get("headline", ""),
        summary=data.get("summary", ""),
        location=data.get("location", ""),
        linkedin_url=data.get("linkedin_url", ""),
        skills=data.get("skills", []),
        experience=experience,
        education=data.get("education", []),
        certifications=data.get("certifications", []),
        raw_text=data.get("raw_text", ""),
    )


def parse_linkedin_pdf(path: Path) -> Profile:
    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return parse_linkedin_text(text)


def parse_linkedin_text(text: str) -> Profile:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    profile = Profile(raw_text=text)

    if not lines:
        return profile

    profile.name = lines[0]
    if len(lines) > 1 and len(lines[1]) < 120:
        profile.headline = lines[1]

    summary_match = re.search(
        r"(?:Summary|About)\s*\n([\s\S]+?)(?:\n(?:Experience|Skills|Education|Certifications)\b|$)",
        text,
        re.IGNORECASE,
    )
    if summary_match:
        profile.summary = summary_match.group(1).strip()

    skills_match = re.search(
        r"(?:Top skills|Skills)\s*\n([\s\S]+?)(?:\n(?:Experience|Education|Certifications)\b|$)",
        text,
        re.IGNORECASE,
    )
    if skills_match:
        block = skills_match.group(1)
        profile.skills = [
            item.strip()
            for item in re.split(r"[\n•,|]", block)
            if item.strip() and len(item.strip()) < 60
        ]

    for match in re.finditer(
        r"(?:^|\n)([A-Za-z0-9 /&.-]{3,80})\s*\n([A-Za-z0-9 &.,'-]{2,80})\s*\n"
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[^\n]*(?:Present|\d{4})[^\n]*)",
        text,
        re.MULTILINE,
    ):
        profile.experience.append(
            Experience(
                title=match.group(1).strip(),
                company=match.group(2).strip(),
                duration=match.group(3).strip(),
            )
        )

    education_match = re.search(
        r"Education\s*\n([\s\S]+?)(?:\n(?:Licenses|Certifications|Skills|Experience)\b|$)",
        text,
        re.IGNORECASE,
    )
    if education_match:
        profile.education = [
            line.strip()
            for line in education_match.group(1).splitlines()
            if line.strip() and len(line.strip()) < 120
        ]

    cert_match = re.search(
        r"(?:Licenses & certifications|Certifications)\s*\n([\s\S]+?)$",
        text,
        re.IGNORECASE,
    )
    if cert_match:
        profile.certifications = [
            line.strip()
            for line in cert_match.group(1).splitlines()
            if line.strip() and len(line.strip()) < 120
        ]

    return profile


def load_profile(
    profile_path: Path,
    pdf_path: Path | None = None,
    text_path: Path | None = None,
) -> Profile:
    if pdf_path and pdf_path.exists():
        return parse_linkedin_pdf(pdf_path)
    if text_path and text_path.exists():
        return parse_linkedin_text(text_path.read_text(encoding="utf-8"))
    if profile_path.exists():
        return load_profile_json(profile_path)
    raise FileNotFoundError(
        f"No profile found. Create {profile_path}, or pass --pdf / --text with LinkedIn export."
    )
