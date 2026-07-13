#!/usr/bin/env bash
# Fraktál — one-line installer
set -euo pipefail

echo "=== Fraktál Installer ==="
echo ""

# Check Python
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python 3.10+ is required."
    exit 1
fi

echo "Using: $PYTHON ($($PYTHON --version))"

# Install in editable mode
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Installing Fraktál from: $PROJECT_DIR"
cd "$PROJECT_DIR"

"$PYTHON" -m pip install -e . --quiet

echo ""
echo "✓ Fraktál installed!"
echo ""
echo "Next steps:"
echo "  1. Set your API key:  export DEEPSEEK_API_KEY='sk-your-key-here'"
echo "  2. Initialize config:  fraktal setup"
echo "  3. Check connection:   fraktal health"
echo "  4. Run your first task: fraktal build 'your task description'"
