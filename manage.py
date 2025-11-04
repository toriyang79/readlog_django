#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Try loading variables from a local .env file if present
try:
    from pathlib import Path
    # Import lazily so this file works even without python-dotenv installed
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        load_dotenv = None

    if 'load_dotenv' in globals() and callable(load_dotenv):
        env_path = Path(__file__).resolve().parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
except Exception:
    # Safe to ignore any issues with optional .env loading
    pass


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'readlog_django.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
