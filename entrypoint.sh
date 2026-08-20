#!/bin/sh

set -e

echo "-> Applying migrations"
python manage.py migrate --noinput

echo "-> Collecting static files"
python manage.py collectstatic --noinput --clear >/dev/null

if [ "${LOAD_DEMO_DATA:-1}" = "1" ]; then
  echo "-> Loading demo data"
  python manage.py seed_demo
fi

if [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  echo "-> Ensuring superuser ${DJANGO_SUPERUSER_EMAIL}"
  python manage.py createsuperuser --noinput --skip-checks 2>/dev/null \
    || echo "   superuser already exists"
fi

echo "-> Starting: $*"
exec "$@"
