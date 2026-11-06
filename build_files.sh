#!/bin/bash
set -e

# Identify available python binary
if command -v python3 &>/dev/null; then
    PY="python3"
elif command -v python &>/dev/null; then
    PY="python"
else
    echo "ERROR: Python binary not found in PATH."
    exit 1
fi

echo "==> Using Python binary: $($PY --version)"

echo "==> Upgrading pip..."
$PY -m pip install --upgrade pip

echo "==> Installing Python Dependencies..."
$PY -m pip install -r requirements.txt

echo "==> Running Database Migrations..."
$PY manage.py migrate --no-input || true

echo "==> Seeding Initial Fleet & User Accounts..."
$PY seed_demo_data.py || true

echo "==> Collecting Static Files..."
$PY manage.py collectstatic --no-input --clear

# Ensure output directory exists for Vercel
mkdir -p staticfiles

echo "==> UTMS Build Complete for Vercel!"
