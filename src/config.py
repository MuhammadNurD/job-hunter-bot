from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from src.paths import resolve_app_path


@dataclass
class AlertConfig:
    console: bool = True
    desktop: bool = False
    email_enabled: bool = False
    email_to: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    webhook_url: str = ""


@dataclass
class SearchConfig:
    allan_gray_careers_url: str = "https://www.allangray.co.za/careers/"
    successfactors_list_url: str = (
        "https://career2.successfactors.eu/career"
        "?company=allangrayp&career_ns=job_listing_summary"
        "&navBarLevel=JOB_SEARCH&rcm_site_locale=en_GB&selected_lang=en_GB"
    )
    web_search_enabled: bool = True
    web_search_queries: list[str] = field(
        default_factory=lambda: [
            "Allan Gray developer jobs Cape Town",
            "Allan Gray software engineer vacancies",
            "site:allangray.co.za developer OR software engineer",
        ]
    )
    developer_keywords: list[str] = field(
        default_factory=lambda: [
            "developer",
            "software",
            "engineer",
            "programmer",
            "devops",
            "full stack",
            "fullstack",
            "backend",
            "frontend",
            "microservices",
            ".net",
            "react",
            "kubernetes",
            "cloud",
            "it analyst",
            "tester",
            "qa",
            "scrum master",
            "business analyst",
            "data engineer",
        ]
    )
    min_match_score: float = 0.35
    poll_interval_hours: float = 6.0


@dataclass
class Config:
    profile_path: Path = Path("profile.json")
    data_dir: Path = Path("data")
    database_path: Path = Path("data/jobs.db")
    alerts: AlertConfig = field(default_factory=AlertConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"


def _resolve_config(config: Config) -> Config:
    config.profile_path = resolve_app_path(config.profile_path)
    config.data_dir = resolve_app_path(config.data_dir)
    config.database_path = resolve_app_path(config.database_path)
    config.data_dir.mkdir(parents=True, exist_ok=True)
    return config


def load_config(path: Path | str | None = None) -> Config:
    config_path = resolve_app_path(path or "config.yaml")
    if not config_path.exists():
        return _resolve_config(Config())

    with config_path.open(encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle) or {}

    alerts_raw = raw.get("alerts", {})
    search_raw = raw.get("search", {})
    email_raw = alerts_raw.get("email", {})
    smtp_password = (
        os.environ.get("JOB_HUNTER_SMTP_PASSWORD")
        or os.environ.get("SMTP_PASSWORD")
        or email_raw.get("smtp_password", "")
    )

    config = Config(
        profile_path=Path(raw.get("profile_path", "profile.json")),
        data_dir=Path(raw.get("data_dir", "data")),
        database_path=Path(raw.get("database_path", "data/jobs.db")),
        alerts=AlertConfig(
            console=alerts_raw.get("console", True),
            desktop=alerts_raw.get("desktop", False),
            email_enabled=email_raw.get("enabled", False),
            email_to=email_raw.get("to", ""),
            smtp_host=email_raw.get("smtp_host", "smtp.gmail.com"),
            smtp_port=int(email_raw.get("smtp_port", 587)),
            smtp_user=email_raw.get("smtp_user", ""),
            smtp_password=smtp_password,
            webhook_url=alerts_raw.get("webhook_url", ""),
        ),
        search=SearchConfig(
            allan_gray_careers_url=search_raw.get(
                "allan_gray_careers_url",
                SearchConfig.allan_gray_careers_url,
            ),
            successfactors_list_url=search_raw.get(
                "successfactors_list_url",
                SearchConfig.successfactors_list_url,
            ),
            web_search_enabled=search_raw.get("web_search_enabled", True),
            web_search_queries=search_raw.get(
                "web_search_queries",
                SearchConfig().web_search_queries,
            ),
            developer_keywords=search_raw.get(
                "developer_keywords",
                SearchConfig().developer_keywords,
            ),
            min_match_score=float(search_raw.get("min_match_score", 0.35)),
            poll_interval_hours=float(search_raw.get("poll_interval_hours", 6.0)),
        ),
        openai_api_key=os.environ.get("OPENAI_API_KEY") or raw.get("openai_api_key", ""),
        openai_model=raw.get("openai_model", "gpt-4o-mini"),
    )
    return _resolve_config(config)
