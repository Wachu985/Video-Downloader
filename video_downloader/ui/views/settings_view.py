"""Advanced settings form bound to the settings repository."""

from __future__ import annotations

from pathlib import Path

import flet as ft

from video_downloader.config.constants import COOKIE_BROWSERS, MAX_CONCURRENT_LIMIT
from video_downloader.ui import theme
from video_downloader.ui.app import AppContext
from video_downloader.ui.components.folder_picker import FolderPicker
from video_downloader.ui.texts import t
from video_downloader.utils.env import find_js_runtime

_THEME_OPTIONS = {
    "system": "theme_system",
    "light": "theme_light",
    "dark": "theme_dark",
}


def _status_card(title: str, detail: str, icon: ft.IconData, color: str) -> ft.Card:
    return ft.Card(
        content=ft.Container(
            padding=14,
            content=ft.Row(
                [
                    ft.Icon(icon, color=color),
                    ft.Column(
                        [
                            ft.Text(title, weight=ft.FontWeight.W_600),
                            ft.Text(detail, size=12),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=12,
            ),
        )
    )


def _parse_headers(raw: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            name, _, value = line.partition(":")
            if name.strip() and value.strip():
                headers[name.strip()] = value.strip()
    return headers


class SettingsView(ft.Column):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 16
        settings = ctx.settings

        # --- FFmpeg status card ------------------------------------------
        location = ctx.ffmpeg.resolve()
        if location.source == "path":
            ffmpeg_text = f"{t('ffmpeg_system')} · {location.ffmpeg_path}"
            ffmpeg_icon, ffmpeg_color = ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN
        elif location.source == "bundled_full":
            ffmpeg_text = t("ffmpeg_bundled_full")
            ffmpeg_icon, ffmpeg_color = ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN
        elif location.source == "bundled":
            ffmpeg_text = t("ffmpeg_bundled")
            ffmpeg_icon, ffmpeg_color = ft.Icons.WARNING, ft.Colors.ORANGE
        else:
            ffmpeg_text = t("ffmpeg_missing")
            ffmpeg_icon, ffmpeg_color = ft.Icons.ERROR, ft.Colors.RED
        ffmpeg_card = _status_card(t("ffmpeg_status"), ffmpeg_text, ffmpeg_icon, ffmpeg_color)

        # --- JS runtime status card (YouTube challenges) -------------------
        runtime = find_js_runtime()
        if runtime:
            name, path = runtime
            js_text = f"{name} · {path} — {t('js_runtime_found')}"
            js_icon, js_color = ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN
        else:
            js_text = t("js_runtime_missing")
            js_icon, js_color = ft.Icons.WARNING, ft.Colors.ORANGE
        js_card = _status_card(t("js_runtime_status"), js_text, js_icon, js_color)

        # --- Form fields ---------------------------------------------------
        self._folder = FolderPicker(settings.download_path)

        self._concurrent_label = ft.Text(
            f"{t('max_concurrent')}: {settings.max_concurrent}"
        )
        self._concurrent = ft.Slider(
            min=1,
            max=MAX_CONCURRENT_LIMIT,
            divisions=MAX_CONCURRENT_LIMIT - 1,
            value=settings.max_concurrent,
            on_change=self._on_concurrent_change,
        )

        self._proxy = ft.TextField(label=t("proxy"), value=settings.proxy, width=420)

        cookie_labels = [t("cookies_none") if b == "" else b for b in COOKIE_BROWSERS]
        self._cookies = ft.Dropdown(
            label=t("cookies_browser"),
            options=[
                ft.DropdownOption(key=browser, text=label)
                for browser, label in zip(COOKIE_BROWSERS, cookie_labels, strict=True)
            ],
            value=settings.cookies_browser,
            width=260,
        )

        self._headers = ft.TextField(
            label=t("custom_headers"),
            value="\n".join(f"{k}: {v}" for k, v in settings.custom_headers.items()),
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=420,
        )
        self._rate_limit = ft.TextField(
            label=t("rate_limit"),
            value=str(settings.rate_limit_kbps),
            width=260,
        )

        self._keep_originals = ft.Switch(
            label=t("keep_originals"), value=settings.keep_originals
        )
        self._subtitles = ft.Switch(
            label=t("subtitles"), value=settings.write_subtitles
        )
        self._subtitle_langs = ft.TextField(
            label=t("subtitle_langs"),
            value=", ".join(settings.subtitle_langs),
            width=260,
        )
        self._thumbnail = ft.Switch(
            label=t("embed_thumbnail"), value=settings.embed_thumbnail
        )
        self._metadata = ft.Switch(
            label=t("embed_metadata"), value=settings.embed_metadata
        )

        self._theme_dd = ft.Dropdown(
            label=t("theme"),
            options=[
                ft.DropdownOption(key=key, text=t(label))
                for key, label in _THEME_OPTIONS.items()
            ],
            value=settings.theme_mode,
            width=200,
            on_select=self._on_theme_change,
        )

        self._saved_text = ft.Text(
            t("saved"), color=ft.Colors.GREEN, visible=False, size=13
        )
        save_button = ft.FilledButton(t("save"), icon=ft.Icons.SAVE, on_click=self._on_save)

        self._picker = ft.FilePicker()
        export_button = ft.OutlinedButton(
            t("export_config"), icon=ft.Icons.UPLOAD, on_click=self._on_export
        )
        import_button = ft.OutlinedButton(
            t("import_config"), icon=ft.Icons.DOWNLOAD, on_click=self._on_import
        )
        self._io_row = ft.Row([export_button, import_button], spacing=12)

        self.controls = [
            ft.Text(t("settings_title"), size=28, weight=ft.FontWeight.BOLD),
            ffmpeg_card,
            js_card,
            self._folder,
            self._concurrent_label,
            self._concurrent,
            ft.Row([self._proxy, self._cookies], spacing=12, wrap=True),
            ft.Row([self._headers, self._rate_limit], spacing=12, wrap=True),
            ft.Row([self._subtitles, self._subtitle_langs], spacing=12, wrap=True),
            ft.Row([self._keep_originals, self._thumbnail, self._metadata], spacing=16, wrap=True),
            self._theme_dd,
            ft.Row([save_button, self._saved_text], spacing=12),
            ft.Divider(),
            self._io_row,
        ]

    def did_mount(self) -> None:
        if self._picker not in self.page.services:
            self.page.services.append(self._picker)

    # ------------------------------------------------------------------

    async def _on_export(self, e: ft.Event) -> None:
        target = await self._picker.save_file(
            dialog_title=t("export_config"),
            file_name="video_downloader_config.json",
            allowed_extensions=["json"],
        )
        if target:
            self.ctx.settings_repo.export_to(Path(target), self.ctx.settings)

    async def _on_import(self, e: ft.Event) -> None:
        files = await self._picker.pick_files(
            dialog_title=t("import_config"), allowed_extensions=["json"]
        )
        if not files or not files[0].path:
            return
        try:
            self.ctx.settings = self.ctx.settings_repo.import_from(Path(files[0].path))
            self.ctx.save_settings()
        except (ValueError, TypeError, OSError):
            return
        self._apply_to_form(self.ctx.settings)
        self.page.theme_mode = theme.theme_mode_from_setting(self.ctx.settings.theme_mode)
        self.page.update()

    def _apply_to_form(self, settings) -> None:
        self._folder.set_value(settings.download_path)
        self._concurrent.value = settings.max_concurrent
        self._concurrent_label.value = f"{t('max_concurrent')}: {settings.max_concurrent}"
        self._proxy.value = settings.proxy
        self._cookies.value = settings.cookies_browser
        self._headers.value = "\n".join(
            f"{k}: {v}" for k, v in settings.custom_headers.items()
        )
        self._rate_limit.value = str(settings.rate_limit_kbps)
        self._keep_originals.value = settings.keep_originals
        self._subtitles.value = settings.write_subtitles
        self._subtitle_langs.value = ", ".join(settings.subtitle_langs)
        self._thumbnail.value = settings.embed_thumbnail
        self._metadata.value = settings.embed_metadata
        self._theme_dd.value = settings.theme_mode

    def _on_concurrent_change(self, e: ft.Event) -> None:
        self._concurrent_label.value = (
            f"{t('max_concurrent')}: {int(self._concurrent.value or 1)}"
        )
        self.update()

    def _on_theme_change(self, e: ft.Event) -> None:
        mode = self._theme_dd.value or "system"
        self.page.theme_mode = theme.theme_mode_from_setting(mode)
        self.page.update()

    def _on_save(self, e: ft.Event) -> None:
        settings = self.ctx.settings
        settings.download_dir = str(self._folder.value)
        settings.max_concurrent = int(self._concurrent.value or 1)
        settings.proxy = (self._proxy.value or "").strip()
        settings.cookies_browser = self._cookies.value or ""
        settings.custom_headers = _parse_headers(self._headers.value or "")
        try:
            settings.rate_limit_kbps = max(0, int(self._rate_limit.value or "0"))
        except ValueError:
            settings.rate_limit_kbps = 0
        settings.keep_originals = bool(self._keep_originals.value)
        settings.write_subtitles = bool(self._subtitles.value)
        settings.subtitle_langs = [
            lang.strip()
            for lang in (self._subtitle_langs.value or "").split(",")
            if lang.strip()
        ] or ["es", "en"]
        settings.embed_thumbnail = bool(self._thumbnail.value)
        settings.embed_metadata = bool(self._metadata.value)
        settings.theme_mode = self._theme_dd.value or "system"

        self.ctx.save_settings()
        self._saved_text.visible = True
        self.update()
