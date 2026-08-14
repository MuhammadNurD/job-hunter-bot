from __future__ import annotations

import sys
from pathlib import Path


def get_app_dir() -> Path:
    """Directory where config, profile, and data files live."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resolve_app_path(path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return get_app_dir() / candidate


def default_config_path() -> Path:
    return get_app_dir() / "config.yaml"


def ensure_runtime_files() -> None:
    app_dir = get_app_dir()
    data_dir = app_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    config_path = app_dir / "config.yaml"
    example_config = app_dir / "config.example.yaml"
    if not config_path.exists() and example_config.exists():
        config_path.write_text(example_config.read_text(encoding="utf-8"), encoding="utf-8")

    profile_path = app_dir / "profile.json"
    example_profile = app_dir / "profile.example.json"
    if not profile_path.exists() and example_profile.exists():
        profile_path.write_text(example_profile.read_text(encoding="utf-8"), encoding="utf-8")
