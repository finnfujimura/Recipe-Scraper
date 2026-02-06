import os
from dotenv import load_dotenv

load_dotenv()


def _parse_csv_env(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(',') if item.strip()]


def _parse_bool_env(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() == 'true'


class Config:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    APP_PASSWORD = os.getenv('APP_PASSWORD')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = _parse_bool_env('FLASK_DEBUG', 'True')

    # CORS: comma-separated list of frontend origins that may call this API.
    FRONTEND_ORIGINS = _parse_csv_env(
        'FRONTEND_ORIGINS',
        'http://localhost:8000,http://127.0.0.1:8000',
    )

    # Session cookie settings for cross-site auth (GitHub Pages -> Cloud Run).
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = _parse_bool_env('SESSION_COOKIE_SECURE', 'False')
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
