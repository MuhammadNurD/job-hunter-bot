from __future__ import annotations

import json
import logging
import platform
import smtplib
import subprocess
from email.message import EmailMessage

import requests

from src.config import AlertConfig
from src.cv.advisor import CvAdvice
from src.matching.matcher import MatchResult

logger = logging.getLogger("job_hunter_bot")


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


def send_test_email(config: AlertConfig) -> None:
    if not config.email_enabled:
        raise ValueError("Email alerts are disabled. Set alerts.email.enabled to true in config.yaml.")
    if not config.email_to:
        raise ValueError("Set alerts.email.to in config.yaml.")

    msg = EmailMessage()
    msg["Subject"] = "Job Hunter Bot test email"
    msg["From"] = config.smtp_user or config.email_to
    msg["To"] = config.email_to
    msg.set_content(
        "Your Job Hunter Bot email alerts are working.\n\n"
        "Leave JobHunterBot.exe running with the watch command to receive job matches."
    )
    _send_smtp(config, msg)
    logger.info("Test email sent to %s", config.email_to)


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
    system = platform.system()
    if system == "Windows":
        _windows_notify(title, url)
        return
    if system == "Linux":
        try:
            subprocess.run(
                ["notify-send", "Job Hunter Bot", f"{title}\n{url}"],
                check=False,
                capture_output=True,
            )
        except FileNotFoundError:
            pass


def _windows_notify(title: str, url: str) -> None:
    try:
        ps_script = (
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
            "ContentType = WindowsRuntime] | Out-Null; "
            "$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(1); "
            "$textNodes = $template.GetElementsByTagName('text'); "
            f"$textNodes.Item(0).AppendChild($template.CreateTextNode('{title.replace(chr(39), '')}')) | Out-Null; "
            f"$textNodes.Item(1).AppendChild($template.CreateTextNode('{url.replace(chr(39), '')[:120]}')) | Out-Null; "
            "$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
            "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Job Hunter Bot').Show($toast);"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            check=False,
            capture_output=True,
        )
    except FileNotFoundError:
        logger.warning("Could not show Windows desktop notification")


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
        logger.exception("Webhook alert failed")


def _email(config: AlertConfig, match: MatchResult, advice: CvAdvice | None) -> None:
    msg = EmailMessage()
    msg["Subject"] = f"Job match: {match.job.title} @ {match.job.company}"
    msg["From"] = config.smtp_user or config.email_to
    msg["To"] = config.email_to
    msg.set_content(_format_message(match, advice))
    try:
        _send_smtp(config, msg)
        logger.info("Email alert sent for %s", match.job.title)
    except smtplib.SMTPException:
        logger.exception("Failed to send email for %s", match.job.title)


def _send_smtp(config: AlertConfig, msg: EmailMessage) -> None:
    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        if config.smtp_user and config.smtp_password:
            server.login(config.smtp_user, config.smtp_password)
        server.send_message(msg)
