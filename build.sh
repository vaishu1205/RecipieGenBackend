#!/usr/bin/env bash
set -o errexit

echo "🐍 Python version:"
python --version

echo "🔧 Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "📊 Checking installed packages..."
pip list | grep -E "(psycopg|Django)"

echo "🔍 Testing database connection..."
python -c "
import os
import django
from django.conf import settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recipe_generator.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'⚠️ Database connection failed: {e}')
"

echo "🔍 Checking Django setup..."
python manage.py check

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "🗃️ Running migrations..."
python manage.py migrate

echo "✅ Build completed!"