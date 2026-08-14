from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Experience:
    title: str
    company: str
    duration: str = ""
    description: str = ""


@dataclass
class Profile:
    name: str = ""
    headline: str = ""
    summary: str = ""
    location: str = ""
    linkedin_url: str = ""
    skills: list[str] = field(default_factory=list)
    experience: list[Experience] = field(default_factory=list)
    education: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    raw_text: str = ""

    def all_text(self) -> str:
        parts = [
            self.name,
            self.headline,
            self.summary,
            self.location,
            " ".join(self.skills),
            " ".join(self.education),
            " ".join(self.certifications),
        ]
        for exp in self.experience:
            parts.extend([exp.title, exp.company, exp.duration, exp.description])
        parts.append(self.raw_text)
        return " ".join(part for part in parts if part).lower()

    def skill_set(self) -> set[str]:
        return {skill.strip().lower() for skill in self.skills if skill.strip()}
