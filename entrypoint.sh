#!/usr/bin/env bash
set -euo pipefail

echo "⏳ Waiting for Postgres at ${POSTGRES_HOST:-${DATABASE_HOST:-localhost}}:${POSTGRES_PORT:-${DATABASE_PORT:-5432}}…"
until pg_isready -q -h "${POSTGRES_HOST:-${DATABASE_HOST:-localhost}}" -p "${POSTGRES_PORT:-${DATABASE_PORT:-5432}}" -U "${POSTGRES_USER:-${DATABASE_USER:-postgres}}"; do
  sleep 1
done
echo "✅ Postgres is up"

# Create tiktoken cache directory in /dev/shm (writable in Fargate)
echo "📁 Creating tiktoken cache directory in /dev/shm"
mkdir -p "${TIKTOKEN_CACHE_DIR:-/dev/shm/tiktoken}" || echo "⚠️ Could not create tiktoken cache directory, continuing..."

: "${DJANGO_SETTINGS_MODULE:=fithub.settings}"

# --- Migrations / seeding (leave as you had) ---
if [[ "${ALLOW_MAKEMIGRATIONS:-0}" == "1" ]]; then
  echo "⚙️ Running makemigrations (dev/staging only)"
  uv run manage.py makemigrations || true
fi

echo "📦 Running migrations"
uv run manage.py migrate --noinput

# AppSettings seeding removed - no users.models.AppSetting in this project

if [[ "${CREATE_SUPERUSER:-0}" == "1" ]]; then
  echo "👤 Ensuring superuser"
  uv run manage.py shell <<PY
from django.contrib.auth import get_user_model
User = get_user_model()
email = "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}"
pwd = "${DJANGO_SUPERUSER_PASSWORD:-ChangeMe123}"
username = "${DJANGO_SUPERUSER_USERNAME:-admin}"

# Check if user exists by email or username
user = None
if User.objects.filter(email=email).exists():
    user = User.objects.get(email=email)
    print(f"📧 Found existing user by email: {email}")
elif User.objects.filter(username=username).exists():
    user = User.objects.get(username=username)
    print(f"👤 Found existing user by username: {username}")

if user:
    # Update existing user
    user.email = email
    user.username = username
    user.set_password(pwd)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"✅ Superuser updated: {email} (username: {username})")
else:
    # Create new superuser
    User.objects.create_superuser(email=email, password=pwd, username=username)
    print(f"✅ Superuser created: {email} (username: {username})")
PY
fi

# --- optional debugpy prefix ---
DEBUGPY_PREFIX=()
if [[ "${DEBUGPY:-0}" == "1" ]]; then
  export DEBUGPY_PORT="${DEBUGPY_PORT:-5678}"
  echo "🔧 debugpy listening on 0.0.0.0:${DEBUGPY_PORT}"
  DEBUGPY_PREFIX=(python -Xfrozen_modules=off -m debugpy ${WAIT_FOR_DEBUGGER:+--wait-for-client} --listen 0.0.0.0:"$DEBUGPY_PORT")
fi

SERVER="${SERVER:-runserver}"
DJANGO_PORT="${DJANGO_PORT:-8000}"

case "$SERVER" in
  daphne)
    echo "🚀 Starting Daphne (ASGI)"
    if [[ "${#DEBUGPY_PREFIX[@]}" -gt 0 ]]; then
      # debugpy -> then launch daphne via python -m daphne
      exec "${DEBUGPY_PREFIX[@]}" -m daphne -b 0.0.0.0 -p "$DJANGO_PORT" fithub.asgi:application
    else
      # no debugpy: still need 'python -m daphne'
      exec python -m daphne -b 0.0.0.0 -p "$DJANGO_PORT" fithub.asgi:application
    fi
    ;;

  gunicorn)
    echo "🚀 Starting Gunicorn (WSGI) with --reload in dev"
    GUNI_WORKERS="${GUNI_WORKERS:-2}"
    GUNI_THREADS="${GUNI_THREADS:-4}"
    EXTRA="${GUNI_EXTRA:---reload --timeout 120 --access-logfile - --error-logfile -}"
    if [[ "${DEBUGPY:-0}" == "1" ]]; then
      exec "${DEBUGPY_PREFIX[@]}" -m gunicorn fithub.wsgi:application --bind 0.0.0.0:"$DJANGO_PORT" \
           --workers "$GUNI_WORKERS" --threads "$GUNI_THREADS" $EXTRA
    else
      exec gunicorn fithub.wsgi:application --bind 0.0.0.0:"$DJANGO_PORT" \
           --workers "$GUNI_WORKERS" --threads "$GUNI_THREADS" $EXTRA
    fi
    ;;

  runserver|*)
    echo "🚀 Starting Django runserver"
    if [[ "${DEBUGPY:-0}" == "1" ]]; then
      exec "${DEBUGPY_PREFIX[@]}" uv run manage.py runserver 0.0.0.0:"$DJANGO_PORT"
    else
      exec uv run manage.py runserver 0.0.0.0:"$DJANGO_PORT"
    fi
    ;;
esac
