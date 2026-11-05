#!/bin/bash
echo "==> Installing Python Dependencies..."
python3.11 -m pip install -r requirements.txt

echo "==> Running Database Migrations..."
python3.11 manage.py migrate --no-input

echo "==> Seeding Initial Fleet & User Accounts..."
python3.11 seed_demo_data.py

echo "==> Collecting Static Files..."
python3.11 manage.py collectstatic --no-input --clear

echo "==> UTMS Build Complete for Vercel!"
