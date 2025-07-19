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

echo "👤 Creating admin user..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'dantinanaresh7432@example.com', 'Naresh@1234')
    print('✅ Admin user created: username=admin, password=Naresh@1234')
else:
    print('ℹ️ Admin user already exists')
"

echo "✅ Build completed!"