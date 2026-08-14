from __future__ import annotations

import json
import smtplib
import subprocess
from email.message import EmailMessage

import requests

from src.config import AlertConfig
from src.cv.advisor import CvAdvice
from src.matching.matcher import MatchResult


def send_alerts(config: AlertConfig, matches: list[MatchResult], advice_map: dict[str, CvAdvice]) -> None:
    for match in matches:
        advice = advice_map.get(match.job.stable_id())
        message = _format_message(match, advice)
        if config.console:
            print(message)
            print("-" * 72)
        if config.desktop:
            _desktop_notify(match.job.title, match.job.apply_url)
        if config.webhook_url:
            _webhook(config.webhook_url, match, advice)
        if config.email_enabled and config.email_to:
            _email(config, match, advice)


def _format_message(match: MatchResult, advice: CvAdvice | None) -> str:
    job = match.job
    lines = [
        f"NEW MATCH ({int(match.score * 100)}%): {job.title} @ {job.company}",
        f"Location: {job.location or 'Not listed'}",
        f"Apply: {job.apply_url}",
    ]
    if job.closing_date:
        lines.append(f"Closing: {job.closing_date}")
    if match.rationale:
        lines.append(f"Why it fits: {match.rationale}")
    if advice:
        lines.append("")
        lines.append("CV suggestions:")
        for tip in advice.suggestions:
            lines.append(f"  - {tip}")
        if advice.summary_line:
            lines.append(f"Suggested summary line: {advice.summary_line}")
    return "\n".join(lines)


def _desktop_notify(title: str, url: str) -> None:
    try:
        subprocess.run(
            ["notify-send", "Job Hunter Bot", f"{title}\n{url}"],
            check=False,
            capture_output=True,
        )
    except FileNotFoundError:
        pass


def _webhook(url: str, match: MatchResult, advice: CvAdvice | None) -> None:
    payload = {
        "text": _format_message(match, advice),
        "job": {
            "title": match.job.title,
            "company": match.job.company,
            "apply_url": match.job.apply_url,
            "score": match.score,
        },
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except requests.RequestException:
        pass


def _email(config: AlertConfig, match: MatchResult, advice: CvAdvice | None) -> None:
    msg = EmailMessage()
    msg["Subject"] = f"Job match: {match.job.title} @ {match.job.company}"
    msg["From"] = config.smtp_user
    msg["To"] = config.email_to
    msg.set_content(_format_message(match, advice))

    with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
        server.starttls()
        if config.smtp_user and config.smtp_password:
            server.login(config.smtp_user, config.smtp_password)
        server.send_message(msg)
