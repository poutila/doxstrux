#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="$(basename "$PWD")"
# VENV_DIR=".venv-.$PROJECT_NAME"

# echo "🔧 Creating virtual environment in $VENV_DIR..."
echo "🔧 Creating virtual environment..."
# uv venv "$VENV_DIR"
uv venv

echo "✅ Virtual environment created."

echo "⚙️  Activating virtual environment..."
# shellcheck disable=SC1090
# source "$VENV_DIR/bin/activate"
source ".venv/bin/activate"

echo "📦 Installing dependencies from pyproject.toml..."
uv pip install -r <(uv pip compile pyproject.toml)

echo "✅ All dependencies installed."

echo ""
# echo "💡 Virtual environment '$VENV_DIR' activated. You're ready to go!"
echo "💡 Virtual environment activated. You're ready to go!"
echo "🧪 To install dev tools: uv pip install -e \".[dev]\""

