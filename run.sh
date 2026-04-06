#!/usr/bin/env bash
# OHW - Oral History Workflow - Quick Launch Script
# Sets up a Python virtual environment and launches the Flet app.

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== OHW — Oral History Workflow ==="
echo

PYTHON_CMD="python3"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
    echo "✓ Virtual environment created"
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo

# Install / upgrade dependencies
echo "Installing dependencies..."
.venv/bin/python -m pip install --upgrade pip --quiet
.venv/bin/python -m pip install -r python_requirements.txt --quiet
echo "✓ Dependencies installed"
echo

# Warn if ffmpeg is missing (required for WAV → MP3 conversion)
if ! command -v ffmpeg &>/dev/null; then
    echo "⚠️  Warning: ffmpeg not found on PATH."
    echo "   WAV-to-MP3 conversion will not work until ffmpeg is installed."
    echo "   macOS:  brew install ffmpeg"
    echo "   Linux:  sudo apt install ffmpeg"
    echo "   Windows: https://ffmpeg.org/download.html"
    echo
fi

# Launch the app
echo "Launching OHW..."
echo
.venv/bin/python app.py
