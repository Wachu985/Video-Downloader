"""Entry point for the Video Downloader desktop app."""

import flet as ft

from video_downloader.core.logging_config import setup_logging
from video_downloader.ui.app import main
from video_downloader.utils.env import ensure_common_paths

if __name__ == "__main__":
    ensure_common_paths()
    setup_logging()
    # Start with the window hidden: the shell reveals it once the frameless
    # UI is fully built, avoiding the native-title-bar flash on launch.
    ft.run(main, assets_dir="assets", view=ft.AppView.FLET_APP_HIDDEN)
