"""Ekstensi Flask yang dibagikan seluruh aplikasi.

Objek dibuat di sini tanpa aplikasi, lalu disambungkan di ``create_app()``.
"""

from flask import jsonify
from flask_login import LoginManager

login_manager = LoginManager()


@login_manager.user_loader
def muat_pengguna(id_pengguna: str):
    """Pulihkan pengguna dari cookie sesi."""
    from app.models.pengguna import Pengguna, ambil_per_id

    try:
        nomor = int(id_pengguna)
    except (TypeError, ValueError):
        return None
    return Pengguna.dari_baris(ambil_per_id(nomor))


@login_manager.unauthorized_handler
def tanpa_sesi():
    """Aplikasi ini hanya melayani JSON: balas 401, jangan alihkan halaman."""
    return (
        jsonify(
            {
                "kode": "TIDAK_LOGIN",
                "pesan": "Sesi tidak ditemukan. Silakan masuk kembali.",
            }
        ),
        401,
    )
