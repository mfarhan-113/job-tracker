#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput