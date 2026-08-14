from __future__ import annotations

import ctypes
import logging
import os
import sys
import threading
from pathlib import Path

from src.bot import watch
from src.config import Config
from src.profile.schema import Profile

logger = logging.getLogger("job_hunter_bot")

_MUTEX_NAME = "Local\\JobHunterBotSingleton"
_mutex_handle = None


def claim_single_instance() -> bool:
    if sys.platform != "win32":
        return True
    global _mutex_handle
    kernel32 = ctypes.windll.kernel32
    _mutex_handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    return kernel32.GetLastError() != 183


def _already_running_dialog() -> None:
    ctypes.windll.user32.MessageBoxW(
        None,
        "Job Hunter Bot is already running.\n\nLook in hidden icons on the taskbar.",
        "Job Hunter Bot",
        0x40,
    )


def _tray_image():
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGBA", (64, 64), (15, 76, 129, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 4, 60, 60), fill=(30, 136, 229, 255))
    try:
        font = ImageFont.truetype("segoeui.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    try:
        draw.text((32, 32), "JH", fill="white", font=font, anchor="mm")
    except TypeError:
        draw.text((18, 20), "JH", fill="white", font=font)
    return image


def _open_path(path: Path) -> None:
    if path.exists():
        os.startfile(path)


def run_with_tray(config: Config, profile: Profile) -> int:
    if not claim_single_instance():
        _already_running_dialog()
        return 0

    import pystray

    stop_event = threading.Event()
    scan_now_event = threading.Event()
    log_path = config.data_dir / "job-hunter.log"

    def on_scan_now(icon, item) -> None:
        logger.info("Scan now requested from tray")
        scan_now_event.set()

    def on_open_log(icon, item) -> None:
        _open_path(log_path)

    def on_open_folder(icon, item) -> None:
        _open_path(config.data_dir)

    def on_stop(icon, item) -> None:
        logger.info("Stop requested from tray")
        stop_event.set()
        icon.stop()

    icon = pystray.Icon(
        "JobHunterBot",
        _tray_image(),
        "Job Hunter Bot",
        menu=pystray.Menu(
            pystray.MenuItem("Job Hunter Bot", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Scan now", on_scan_now),
            pystray.MenuItem("Open log", on_open_log),
            pystray.MenuItem("Open data folder", on_open_folder),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Stop", on_stop),
        ),
    )

    worker = threading.Thread(
        target=watch,
        kwargs={
            "config": config,
            "profile": profile,
            "stop_event": stop_event,
            "scan_now_event": scan_now_event,
        },
        daemon=True,
        name="job-hunter-watch",
    )
    worker.start()
    logger.info("Tray icon started")
    icon.run()
    stop_event.set()
    return 0
