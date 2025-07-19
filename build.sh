#!/usr/bin/env bash
set -o errexit

echo "🐍 Python version:"
python --version

echo "🔧 Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🔍 Checking Django setup..."
python manage.py check --deploy --settings=recipe_generator.settings

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "🗃️ Running migrations..."
python manage.py migrate

echo "✅ Build completed!"