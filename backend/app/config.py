"""Konfigurasi aplikasi, dibaca sekali dari berkas ``.env``.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 8 (batas berkas, masa berlaku
token), 14 (cookie sesi), dan 15 (daftar variabel lingkungan).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

AKAR_BACKEND = Path(__file__).resolve().parent.parent
AKAR_PROYEK = AKAR_BACKEND.parent

# .env berada di akar proyek, sejajar dengan .env.example.
load_dotenv(AKAR_PROYEK / ".env")


def _bool_env(nama: str, bawaan: bool = False) -> bool:
    nilai = (os.environ.get(nama) or "").strip().lower()
    if not nilai:
        return bawaan
    return nilai in ("1", "true", "yes", "on")


class Config:
    """Nilai konfigurasi yang dipakai ``create_app()``."""

    # --- Database ---
    DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()

    # --- Sesi ---
    SECRET_KEY = (os.environ.get("SECRET_KEY") or "").strip()
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Aktifkan hanya bila aplikasi dilayani lewat HTTPS; kalau tidak, cookie
    # tidak akan pernah terkirim saat pengembangan lokal di http://localhost.
    SESSION_COOKIE_SECURE = _bool_env("SESSION_COOKIE_SECURE", False)

    # --- Unggahan ---
    UPLOAD_TMP_DIR = Path(
        (os.environ.get("UPLOAD_TMP_DIR") or "").strip() or (AKAR_PROYEK / "uploads_tmp")
    )
    # Bagian 8: maksimal 10 MB.
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    EKSTENSI_DIIZINKAN = (".xlsx", ".xls")
    # Bagian 8: berkas sementara kedaluwarsa 30 menit.
    TOKEN_KEDALUWARSA_DETIK = 30 * 60

    JSON_SORT_KEYS = False

    @classmethod
    def periksa(cls) -> None:
        """Hentikan lebih awal bila konfigurasi wajib belum diisi."""
        kurang = [
            nama
            for nama in ("DATABASE_URL", "SECRET_KEY")
            if not getattr(cls, nama)
        ]
        if kurang:
            raise RuntimeError(
                "Variabel lingkungan berikut belum diisi: "
                + ", ".join(kurang)
                + f". Salin {AKAR_PROYEK / '.env.example'} menjadi .env lalu lengkapi."
            )
