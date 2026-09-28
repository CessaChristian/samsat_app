"""Konfigurasi aplikasi, dibaca sekali dari ``backend/.env``.

Backend dan frontend memakai berkas ``.env`` masing-masing: yang di sini
memuat rahasia (koneksi database, kunci sesi) dan tidak pernah sampai ke
peramban, sedangkan ``frontend/.env`` hanya memuat alamat.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 8 (batas berkas, masa berlaku
token), 14 (cookie sesi), dan 15 (daftar variabel lingkungan).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

AKAR_BACKEND = Path(__file__).resolve().parent.parent
AKAR_PROYEK = AKAR_BACKEND.parent

load_dotenv(AKAR_BACKEND / ".env")


def _bool_env(nama: str, bawaan: bool = False) -> bool:
    nilai = (os.environ.get(nama) or "").strip().lower()
    if not nilai:
        return bawaan
    return nilai in ("1", "true", "yes", "on")


def _int_env(nama: str, bawaan: int) -> int:
    nilai = (os.environ.get(nama) or "").strip()
    if not nilai:
        return bawaan
    try:
        return int(nilai)
    except ValueError as exc:
        raise RuntimeError(f"{nama} harus berupa angka, bukan \"{nilai}\".") from exc


def _folder_env(nama: str, bawaan: Path) -> Path:
    """Lintasan relatif dihitung dari folder backend, bukan folder kerja."""
    nilai = (os.environ.get(nama) or "").strip()
    if not nilai:
        return bawaan
    path = Path(nilai)
    return path if path.is_absolute() else (AKAR_BACKEND / path).resolve()


class Config:
    """Nilai konfigurasi yang dipakai ``create_app()``."""

    # --- Database ---
    DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()

    # --- Sesi ---
    SECRET_KEY = (os.environ.get("SECRET_KEY") or "").strip()
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool_env("SESSION_COOKIE_SECURE", False)

    # --- Server pengembangan (python3 main.py) ---
    HOST = (os.environ.get("HOST") or "").strip() or "127.0.0.1"
    PORT = _int_env("PORT", 5000)
    DEBUG = _bool_env("DEBUG", False)

    # --- Tampilan ---
    # Hasil "npm run build". Disajikan langsung oleh Flask supaya satu
    # perintah sudah melayani tampilan dan API di alamat yang sama.
    FOLDER_FRONTEND = _folder_env(
        "FOLDER_FRONTEND", AKAR_PROYEK / "frontend" / "dist"
    )

    # --- Unggahan ---
    UPLOAD_TMP_DIR = _folder_env("UPLOAD_TMP_DIR", AKAR_BACKEND / "uploads_tmp")
    # Bagian 8: maksimal 10 MB.
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    EKSTENSI_DIIZINKAN = (".xlsx", ".xls")
    # Bagian 8: berkas sementara kedaluwarsa 30 menit.
    TOKEN_KEDALUWARSA_DETIK = 30 * 60


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
                + f". Salin {AKAR_BACKEND / '.env.example'} menjadi "
                + f"{AKAR_BACKEND / '.env'} lalu lengkapi."
            )
