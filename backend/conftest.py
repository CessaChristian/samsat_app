"""Fixture bersama untuk pengujian.

Tes yang menyentuh database memakai database **terpisah** yang ditunjuk
``TEST_DATABASE_URL``. Isinya dikosongkan sebelum setiap tes, jadi database
itu tidak boleh sama dengan database aplikasi.

Bila ``TEST_DATABASE_URL`` kosong, tes-tes tersebut dilewati sehingga suite
tetap dapat dijalankan tanpa PostgreSQL.
"""

import os

import pytest

from app.config import Config  # impor ini sekaligus memuat berkas .env

TEST_DATABASE_URL = (os.environ.get("TEST_DATABASE_URL") or "").strip()

#: Dikosongkan sebelum setiap tes. dim_wilayah sengaja tidak ikut: isinya
#: master, bukan data unggahan.
TABEL_DATA = ("kewajiban_pkb", "ingest_batch", "pengguna")


@pytest.fixture(scope="session")
def url_uji() -> str:
    """URL database uji, skemanya sudah dipastikan terpasang."""
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL belum diisi di .env")

    if TEST_DATABASE_URL == Config.DATABASE_URL:
        raise RuntimeError(
            "TEST_DATABASE_URL sama dengan DATABASE_URL. Pengujian mengosongkan "
            "tabel data, jadi menolak berjalan di database aplikasi."
        )

    from app.utils.migrasi import jalankan_migrasi

    jalankan_migrasi(TEST_DATABASE_URL)
    return TEST_DATABASE_URL


@pytest.fixture
def db(url_uji, monkeypatch):
    """Modul ``app.database`` yang menunjuk database uji yang sudah dikosongkan."""
    import psycopg

    from app import database

    database.tutup_pool()
    monkeypatch.setattr(Config, "DATABASE_URL", url_uji)

    # Nama tabel berasal dari konstanta di berkas ini, bukan dari input pengguna.
    with psycopg.connect(url_uji, autocommit=True) as conn:
        conn.execute(f"TRUNCATE {', '.join(TABEL_DATA)} RESTART IDENTITY CASCADE")

    yield database

    database.tutup_pool()


@pytest.fixture
def koneksi_uji(url_uji):
    """Koneksi mentah ke database uji untuk memeriksa hasil penyimpanan."""
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(url_uji, row_factory=dict_row) as conn:
        yield conn


@pytest.fixture
def app(db, tmp_path):
    """Aplikasi Flask yang menunjuk database uji dan folder unggahan sementara."""
    from app import create_app

    aplikasi = create_app()
    aplikasi.config.update(
        TESTING=True,
        SECRET_KEY="kunci-untuk-pengujian",
        UPLOAD_TMP_DIR=tmp_path / "uploads_tmp",
    )
    return aplikasi


@pytest.fixture
def klien(app):
    return app.test_client()


@pytest.fixture
def pengguna_uji(db):
    """Satu akun petugas untuk menguji alur login."""
    from werkzeug.security import generate_password_hash

    from app.models import pengguna as model

    model.buat("petugas", generate_password_hash("rahasia123"))
    return {"username": "petugas", "password": "rahasia123"}


@pytest.fixture
def klien_masuk(klien, pengguna_uji):
    """Klien yang sudah memegang sesi petugas."""
    klien.post(
        "/api/auth/login",
        json={"username": pengguna_uji["username"], "password": pengguna_uji["password"]},
    )
    return klien
