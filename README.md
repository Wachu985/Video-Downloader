# Video Downloader

Advanced desktop media download manager built with [Flet](https://flet.dev)
(Flutter-powered UI), [yt-dlp](https://github.com/yt-dlp/yt-dlp) (download
engine) and FFmpeg (media processing).

## Features

- URL analysis: single videos, playlists and channels.
- Format explorer: resolution, FPS, codecs, bitrate and estimated size.
- Download modes: video only, audio only (MP3/M4A/AAC/FLAC/OPUS/WAV), or
  video+audio with automatic merging via FFmpeg.
- Post-download conversion with lossless remux vs re-encode detection.
- Concurrent downloads with queue, live progress, speed, ETA and cancellation.
- Advanced settings: proxy, browser cookies, custom headers, rate limiting,
  subtitles, thumbnails and metadata embedding.
- Custom "Nocturnal Studio" design system: frameless window with in-app
  controls, dark/light themes, custom sidebar and live download badge.

## Requirements

- [uv](https://docs.astral.sh/uv/) (manages Python 3.13 and all dependencies
  automatically).
- FFmpeg is optional: if it is not on the `PATH`, the app uses the bundled
  `static-ffmpeg` toolchain (ffmpeg + ffprobe, downloaded once in the
  background) and, as a last resort, the `imageio-ffmpeg` binary (no ffprobe).
  A system FFmpeg (`brew install ffmpeg`) always takes priority.
- **YouTube** needs a JavaScript engine to solve its challenges (EJS):
  `brew install deno` (recommended; node or bun also work). The solver
  scripts ship with the `yt-dlp-ejs` package. YouTube also tends to require a
  session: configure **Settings → Browser cookies**. The Settings screen
  shows the status of both FFmpeg and the JS engine.

## Run from source

```bash
uv sync
uv run python main.py          # desktop app
uv run flet run --web main.py  # browser mode (development)
```

## Tests and quality

```bash
uv run pytest
uv run ruff check .
uv run mypy video_downloader
```

## Building executables

`flet build` packages the app with Flutter and **only compiles for the OS it
runs on** (there is no cross-compilation). Branding comes from the repo:

- Product name: `[tool.flet] product` in [pyproject.toml](pyproject.toml)
  (`Video Downloader`).
- App icon: [assets/icon.png](assets/icon.png) — flet generates every
  platform-specific icon size from it (.icns, .ico, etc.).
- App version: `[project] version` in [pyproject.toml](pyproject.toml).

### Local build (current OS only)

```bash
# On macOS   → build/macos/Video Downloader.app
uv run flet build macos --yes

# On Windows → build/windows/  (Video Downloader.exe + support files)
uv run flet build windows --yes

# On Linux   → build/linux/
uv run flet build linux --yes
```

Notes:

- `--yes` lets flet download the exact Flutter SDK version it requires
  (~1 GB the first time; cached afterwards). The Flutter version is
  determined by the pinned flet release in `uv.lock`, so builds are
  reproducible.
- Linux needs build dependencies first:
  `sudo apt-get install ninja-build libgtk-3-dev libmpv-dev mpv`.
- Windows needs Visual Studio Build Tools with the "Desktop development
  with C++" workload.

### Release builds for all three platforms (GitHub Actions)

The workflow [.github/workflows/build.yml](.github/workflows/build.yml)
builds macOS, Windows and Linux in parallel on GitHub-hosted runners.

**To publish a release:**

```bash
# 1. Bump [project] version in pyproject.toml (e.g. 0.2.0), commit, then:
git tag v0.2.0
git push origin v0.2.0

# 2. Create the GitHub release for that tag (or let the workflow create it):
gh release create v0.2.0 --title "v0.2.0" --generate-notes
```

Pushing the `v*` tag triggers the workflow, which builds the three
platforms and attaches the packaged binaries to the release for that tag:

- `VideoDownloader-macos.zip` (`Video Downloader.app`)
- `VideoDownloader-windows.zip`
- `VideoDownloader-linux.tar.gz`

You can also run it manually from the **Actions** tab (workflow_dispatch);
manual runs upload the binaries as workflow artifacts instead of attaching
them to a release.

**Version pinning policy:** everything in the workflow is pinned on purpose —
GitHub Actions by exact tag, the uv version, Python from `.python-version`,
project dependencies via `uv sync --frozen` (installs exactly what `uv.lock`
records, never re-resolves), and the Flutter SDK via the pinned flet release.
Nothing updates by itself; bump versions manually when you decide to.

## Architecture

```
video_downloader/
├── config/     # constants, presets and settings persistence (JSON)
├── core/       # errors, typed events, event bus (threads → UI) and logging
├── models/     # MediaInfo/FormatInfo/PlaylistInfo, DownloadTask/Request, conversion
├── services/   # ytdlp_service, ffmpeg_service, format_builder, download_manager
├── utils/      # human formatting, URL validation, paths
└── ui/         # Flet shell, views, components, theme and texts (Spanish)
```

Key design rules:

- yt-dlp is blocking: it runs on `DownloadManager` worker threads; no Flet
  control is ever touched from those threads. Events cross into the UI loop
  through the `EventBus`.
- `format_builder` is pure (UI options → `ydl_opts`) and concentrates the
  test suite.
- The UI only shows Spanish messages mapped from the error taxonomy; the
  technical detail goes to the log (`~/Library/Logs/VideoDownloader/`).
