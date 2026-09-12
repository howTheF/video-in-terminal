#!/usr/bin/env bash
set -euo pipefail

echo "Setting up video-in-terminal..."

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 not found. Install it first (e.g. 'brew install python3')." >&2
    exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffplay >/dev/null 2>&1; then
    echo "ffmpeg/ffplay not found."
    if command -v brew >/dev/null 2>&1; then
        echo "Installing ffmpeg via Homebrew..."
        brew install ffmpeg
    elif command -v apt-get >/dev/null 2>&1; then
        echo "Installing ffmpeg via apt-get..."
        sudo apt-get update && sudo apt-get install -y ffmpeg
    else
        echo "Please install ffmpeg manually (needed for audio playback)." >&2
    fi
fi

python3 -m pip install --upgrade pip
python3 -m pip install -r "$(dirname "$0")/requirements.txt"

echo "Done. Try: python3 play.py your_video.mp4"
