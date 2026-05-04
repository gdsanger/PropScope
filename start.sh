#!/bin/bash
set -e

cd /Users/admin/PropScope

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export PYTHONUNBUFFERED=1
export DJANGO_SETTINGS_MODULE=propscope.settings

source venv/bin/activate

exec venv/bin/gunicorn \
    propscope.wsgi:application \
    --bind 0.0.0.0:8008 \
    --workers 2 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
