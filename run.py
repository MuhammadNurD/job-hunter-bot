#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.bot import ensure_profile, run_scan, watch
from src.config import load_config
from src.storage.database import JobDatabase


def cmd_scan(args: argparse.Namespace) -> int:
    config = load_config(args.config)
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
        Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote report to {args.report}")
    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    config = load_config(args.config)
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
        Path(args.save).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Saved profile to {args.save}")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    profile = ensure_profile(config, args.pdf, args.text)
    watch(config, profile)
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    db = JobDatabase(config.database_path)
    rows = db.list_jobs()
    if args.export:
        db.export_json(Path(args.export))
        print(f"Exported {len(rows)} jobs to {args.export}")
    else:
        print(json.dumps(rows, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Job Hunter Bot: Allan Gray developer job scanner with CV advice and alerts."
    )
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
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

    watch_cmd = sub.add_parser("watch", help="Continuously poll for new jobs")
    watch_cmd.set_defaults(func=cmd_watch)

    history = sub.add_parser("history", help="Show previously seen jobs")
    history.add_argument("--export", help="Export job history to JSON file")
    history.set_defaults(func=cmd_history)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
