#!/usr/bin/env bash
set -o errexit

echo "🔧 Installing system dependencies..."
apt-get update
apt-get install -y libpq-dev python3-dev gcc

echo "📦 Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "🔍 Checking Django setup..."
python manage.py check

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "🗃️ Running migrations..."
python manage.py migrate

echo "✅ Build completed!"