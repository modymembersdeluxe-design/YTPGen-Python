# YTPGen Python Generator Backend

`ytpgen_py_generator.py` is a modular auxiliary backend generator script for **YTPGen Mega — v0.9.5 (build 250) — Beta 1**.

It is designed for:

- Python 3.8 (Windows 7 / Windows 8.1 compatible)
- MoviePy 1.0.1
- External FFmpeg available in `PATH` or local working folder

## Features

- Recursive media scanning (video/image/audio libraries)
- Randomized clip slicing from source videos
- Meme-style randomized video effects
- Randomized/filtered audio effects with FFmpeg fallback
- Mode presets:
  - `STANDARD`
  - `YTPMV`
  - `TENNIS`
  - `COLLAB`
- Concatenation pipeline using MoviePy (`compose` mode)
- Final encoding and normalization via FFmpeg subprocess
- Optional `.ytpproj.json` metadata export

## Supported Media Types

- Video: `.mp4`, `.wmv`, `.avi`, `.mkv`
- Image: `.png`, `.jpg`, `.jpeg`, `.webp`
- Audio: `.mp3`, `.wav`, `.ogg`

## Quick Start

### 1) Install dependencies

```bash
pip install moviepy==1.0.1
```

Ensure `ffmpeg` is installed and available in `PATH`.

### 2) Run generator

```bash
python ytpgen_py_generator.py \
  --source "C:\\YTPGen\\SourceMedia" \
  --output "C:\\YTPGen\\Output\\ytp_render.mp4" \
  --mode STANDARD \
  --clip-count 25 \
  --min-duration 0.4 \
  --max-duration 2.2 \
  --resolution 1280x720 \
  --format mp4 \
  --bitrate 3000k \
  --export-metadata
```

## Command-Line Arguments

- `--source` (required): Source media folder
- `--output` (required): Output video file path
- `--mode`: `STANDARD`, `YTPMV`, `TENNIS`, `COLLAB`
- `--clip-count`: Number of generated clip units
- `--min-duration`: Minimum random clip duration
- `--max-duration`: Maximum random clip duration
- `--resolution`: Target output resolution (`WIDTHxHEIGHT`)
- `--no-video-effects`: Disable random video effects
- `--no-audio-effects`: Disable random audio effects
- `--audio-library`: Optional extra folder for overlay sounds
- `--format`: `mp4`, `wmv`, `avi`, `mkv`
- `--bitrate`: Final video bitrate (e.g. `2500k`)
- `--export-metadata`: Export compatible `.ytpproj.json`
- `--project-name`: Metadata project name
- `--bpm`: Base BPM used by `YTPMV` sync simulation
- `--temp-folder`: Optional temp directory override
- `--scale`: Optional FFmpeg scale override (e.g. `854:480`)

## Output Artifacts

- Final rendered video in selected container/format
- Optional metadata JSON beside output file:
  - `*.ytpproj.json`

## Notes

- Corrupt or unsupported files are skipped with warnings.
- Missing FFmpeg causes a startup error.
- Temporary files are cleaned automatically at the end of execution.
