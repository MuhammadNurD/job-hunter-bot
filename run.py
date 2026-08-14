#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.alerts.notifier import send_test_email
from src.bot import ensure_profile, run_scan, watch
from src.config import load_config
from src.logging_setup import setup_logging
from src.paths import default_config_path, ensure_runtime_files, get_app_dir
from src.storage.database import JobDatabase


def _prepare_runtime(args: argparse.Namespace, quiet_console: bool = False):
    ensure_runtime_files()
    config = load_config(args.config or default_config_path())
    log_path = config.data_dir / "job-hunter.log"
    logger = setup_logging(log_path, quiet_console=quiet_console)
    return config, logger


def cmd_scan(args: argparse.Namespace) -> int:
    config, _ = _prepare_runtime(args)
    profile = ensure_profile(config, args.pdf, args.text)
    matches, summary = run_scan(config, profile, alert_new_only=not args.all)

    print("\nScan summary:")
    print(json.dumps(summary, indent=2))

    if args.report:
        report = []
        for match in matches:
            report.append(
                {
                    "title": match.job.title,
                    "company": match.job.company,
                    "score": match.score,
                    "apply_url": match.job.apply_url,
                    "location": match.job.location,
                    "closing_date": match.job.closing_date,
                    "rationale": match.rationale,
                }
            )
        report_path = Path(args.report)
        if not report_path.is_absolute():
            report_path = get_app_dir() / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote report to {report_path}")
    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    config, _ = _prepare_runtime(args)
    profile = ensure_profile(config, args.pdf, args.text)
    payload = {
        "name": profile.name,
        "headline": profile.headline,
        "summary": profile.summary,
        "location": profile.location,
        "linkedin_url": profile.linkedin_url,
        "skills": profile.skills,
        "experience": [
            {
                "title": exp.title,
                "company": exp.company,
                "duration": exp.duration,
                "description": exp.description,
            }
            for exp in profile.experience
        ],
        "education": profile.education,
        "certifications": profile.certifications,
    }
    print(json.dumps(payload, indent=2))
    if args.save:
        save_path = Path(args.save)
        if not save_path.is_absolute():
            save_path = get_app_dir() / save_path
        save_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Saved profile to {save_path}")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    config, logger = _prepare_runtime(args, quiet_console=getattr(sys, "frozen", False))
    profile = ensure_profile(config, args.pdf, args.text)
    logger.info("Using app directory: %s", get_app_dir())
    if sys.platform == "win32":
        from src.tray import run_with_tray

        return run_with_tray(config, profile)
    watch(config, profile)
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    config, _ = _prepare_runtime(args)
    db = JobDatabase(config.database_path)
    rows = db.list_jobs()
    if args.export:
        export_path = Path(args.export)
        if not export_path.is_absolute():
            export_path = get_app_dir() / export_path
        db.export_json(export_path)
        print(f"Exported {len(rows)} jobs to {export_path}")
    else:
        print(json.dumps(rows, indent=2))
    return 0


def cmd_test_email(args: argparse.Namespace) -> int:
    config, logger = _prepare_runtime(args)
    try:
        send_test_email(config.alerts)
        print(f"Test email sent to {config.alerts.email_to}")
        return 0
    except (ValueError, Exception) as exc:
        logger.exception("Test email failed")
        print(f"Test email failed: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Job Hunter Bot: Allan Gray developer job scanner with CV advice and alerts."
    )
    parser.add_argument(
        "--config",
        default=str(default_config_path()),
        help="Path to config.yaml (defaults to folder containing the exe/script)",
    )
    parser.add_argument("--pdf", type=Path, help="LinkedIn profile PDF export")
    parser.add_argument("--text", type=Path, help="Plain-text LinkedIn profile paste")

    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Run one job scan now")
    scan.add_argument("--all", action="store_true", help="Alert for all matches, not only new jobs")
    scan.add_argument("--report", help="Write JSON report of matches to this path")
    scan.set_defaults(func=cmd_scan)

    profile = sub.add_parser("profile", help="Parse and show your LinkedIn profile")
    profile.add_argument("--save", help="Save parsed profile JSON to this path")
    profile.set_defaults(func=cmd_profile)

    watch_cmd = sub.add_parser("watch", help="Run in the background and poll for new jobs")
    watch_cmd.set_defaults(func=cmd_watch)

    history = sub.add_parser("history", help="Show previously seen jobs")
    history.add_argument("--export", help="Export job history to JSON file")
    history.set_defaults(func=cmd_history)

    test_email = sub.add_parser("test-email", help="Send a test email using SMTP settings")
    test_email.set_defaults(func=cmd_test_email)

    return parser


def main() -> int:
    commands = {"scan", "profile", "watch", "history", "test-email"}
    if not any(arg in commands for arg in sys.argv[1:]):
        sys.argv.append("watch")
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
