"""Card showing analyzed media metadata (thumbnail, title, author, duration)."""

from __future__ import annotations

import flet as ft

from video_downloader.models.media import MediaInfo, PlaylistInfo
from video_downloader.ui.texts import t
from video_downloader.utils.formatting import human_duration


class MediaCard(ft.Card):
    def __init__(self, media: MediaInfo | PlaylistInfo) -> None:
        super().__init__()
        is_playlist = isinstance(media, PlaylistInfo)

        thumbnail: ft.Control
        if media.thumbnail_url:
            thumbnail = ft.Image(
                src=media.thumbnail_url,
                width=200,
                height=112,
                fit=ft.BoxFit.COVER,
                border_radius=ft.BorderRadius.all(8),
            )
        else:
            thumbnail = ft.Container(
                width=200,
                height=112,
                border_radius=ft.BorderRadius.all(8),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                content=ft.Icon(
                    ft.Icons.PLAYLIST_PLAY if is_playlist else ft.Icons.MOVIE,
                    size=48,
                ),
                alignment=ft.Alignment.CENTER,
            )

        details: list[ft.Control] = [
            ft.Text(
                media.title,
                size=18,
                weight=ft.FontWeight.BOLD,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        ]
        if media.uploader:
            details.append(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.PERSON, size=16),
                        ft.Text(media.uploader, size=14),
                    ],
                    spacing=6,
                )
            )
        if isinstance(media, PlaylistInfo):
            details.append(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.PLAYLIST_PLAY, size=16),
                        ft.Text(
                            f"{media.entry_count} {t('videos_found')}",
                            size=14,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    spacing=6,
                )
            )
        else:
            details.append(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SCHEDULE, size=16),
                        ft.Text(human_duration(media.duration), size=14),
                    ],
                    spacing=6,
                )
            )

        self.content = ft.Container(
            padding=16,
            content=ft.Row(
                [
                    thumbnail,
                    ft.Column(
                        details,
                        spacing=8,
                        expand=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
