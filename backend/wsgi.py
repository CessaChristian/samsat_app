"""Titik masuk WSGI untuk Gunicorn.

    gunicorn --timeout 120 --chdir backend wsgi:app

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 2 dan 15.
"""

from app import create_app

app = create_app()
