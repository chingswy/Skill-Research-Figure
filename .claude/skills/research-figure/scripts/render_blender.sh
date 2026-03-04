#!/bin/bash
# render_blender.sh — Invoke Blender to run a Python render script
# Usage: render_blender.sh <script.py> [-- extra_args...]
# Exit codes: 0=success, 1=Blender not found, 2=script error

set -euo pipefail

SCRIPT="${1:?Usage: render_blender.sh <script.py> [-- extra_args...]}"
shift

if [[ ! -f "$SCRIPT" ]]; then
    echo "ERROR: Script not found: $SCRIPT"
    exit 2
fi

# --- Auto-discover Blender ---
BLENDER=""

# 1. Environment variable
if [[ -n "${BLENDER_PATH:-}" ]] && [[ -x "$BLENDER_PATH" ]]; then
    BLENDER="$BLENDER_PATH"
fi

# 2. Common macOS paths (newest first)
if [[ -z "$BLENDER" ]]; then
    for app in /Applications/Blender*.app/Contents/MacOS/Blender; do
        if [[ -x "$app" ]]; then
            BLENDER="$app"
            break
        fi
    done
fi

# 3. Homebrew cask (macOS)
if [[ -z "$BLENDER" ]] && [[ -x "/opt/homebrew/bin/blender" ]]; then
    BLENDER="/opt/homebrew/bin/blender"
fi

# 4. PATH lookup
if [[ -z "$BLENDER" ]] && command -v blender &>/dev/null; then
    BLENDER="$(command -v blender)"
fi

if [[ -z "$BLENDER" ]]; then
    echo "ERROR: Blender not found."
    echo "Install Blender and either:"
    echo "  1. Set BLENDER_PATH=/path/to/blender"
    echo "  2. Install to /Applications/ (macOS)"
    echo "  3. Add blender to your PATH"
    exit 1
fi

echo "Using Blender: $BLENDER"

# --- Set PYTHONPATH to include blender_utils parent ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
export PYTHONPATH="${SKILL_DIR}:${PYTHONPATH:-}"
echo "PYTHONPATH includes: $SKILL_DIR"

# --- Run Blender ---
echo "Running: $SCRIPT"
echo "=========================================="

RENDER_LOG=$(mktemp /tmp/blender_render_XXXXXX.log)

if "$BLENDER" --background -noaudio --python "$SCRIPT" -- "$@" 2>&1 | tee "$RENDER_LOG"; then
    echo "=========================================="
    echo "Render completed successfully."

    # Try to find output file path from log
    OUTPUT=$(grep -oE 'Output: .+' "$RENDER_LOG" | tail -1 | sed 's/Output: //' || true)
    if [[ -n "$OUTPUT" ]] && [[ -f "$OUTPUT" ]]; then
        echo "Output file: $OUTPUT"
    fi

    rm -f "$RENDER_LOG"
    exit 0
else
    EXIT_CODE=$?
    echo "=========================================="
    echo "ERROR: Blender script failed (exit code $EXIT_CODE)"
    echo "--- Last 30 lines of output ---"
    tail -30 "$RENDER_LOG"
    rm -f "$RENDER_LOG"
    exit 2
fi
