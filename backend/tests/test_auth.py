"""Tes untuk login dan penjagaan sesi.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 11 (Auth) dan 14 (Login).
Semua endpoint selain login wajib sesi; tanpa sesi harus 401, bukan
pengalihan ke halaman login.
"""

import pytest


def test_login_dengan_kredensial_benar(klien, pengguna_uji):
    balasan = klien.post(
        "/api/auth/login",
        json={"username": pengguna_uji["username"], "password": pengguna_uji["password"]},
    )

    assert balasan.status_code == 200
    assert balasan.get_json() == {"username": "petugas"}


def test_login_dengan_kata_sandi_salah_ditolak(klien, pengguna_uji):
    balasan = klien.post(
        "/api/auth/login",
        json={"username": pengguna_uji["username"], "password": "salah"},
    )

    assert balasan.status_code == 401


def test_login_dengan_username_tidak_terdaftar_ditolak(klien, pengguna_uji):
    balasan = klien.post(
        "/api/auth/login", json={"username": "bukan-siapa-siapa", "password": "rahasia123"}
    )

    assert balasan.status_code == 401


def test_pesan_gagal_tidak_membocorkan_username_mana_yang_ada(klien, pengguna_uji):
    """Balasan untuk username salah dan kata sandi salah harus seragam."""
    salah_sandi = klien.post(
        "/api/auth/login", json={"username": "petugas", "password": "salah"}
    )
    salah_nama = klien.post(
        "/api/auth/login", json={"username": "tidak-ada", "password": "rahasia123"}
    )

    assert salah_sandi.get_json() == salah_nama.get_json()


@pytest.mark.parametrize(
    "muatan",
    [{}, {"username": "petugas"}, {"password": "rahasia123"}, {"username": "", "password": ""}],
)
def test_login_tanpa_kredensial_lengkap_ditolak(klien, pengguna_uji, muatan):
    balasan = klien.post("/api/auth/login", json=muatan)

    assert balasan.status_code in (400, 401)


def test_me_tanpa_sesi_menghasilkan_401(klien):
    assert klien.get("/api/auth/me").status_code == 401


def test_me_setelah_login_menyebut_pengguna(klien, pengguna_uji):
    klien.post(
        "/api/auth/login",
        json={"username": pengguna_uji["username"], "password": pengguna_uji["password"]},
    )

    balasan = klien.get("/api/auth/me")

    assert balasan.status_code == 200
    assert balasan.get_json() == {"username": "petugas"}


def test_logout_mengakhiri_sesi(klien, pengguna_uji):
    klien.post(
        "/api/auth/login",
        json={"username": pengguna_uji["username"], "password": pengguna_uji["password"]},
    )

    keluar = klien.post("/api/auth/logout")

    assert keluar.status_code == 204
    assert klien.get("/api/auth/me").status_code == 401


def test_logout_tanpa_sesi_tetap_aman(klien):
    assert klien.post("/api/auth/logout").status_code in (204, 401)


def test_balasan_401_berupa_json_bukan_pengalihan(klien):
    balasan = klien.get("/api/auth/me")

    assert balasan.status_code == 401
    assert balasan.is_json
    assert "kode" in balasan.get_json()


def test_kata_sandi_tidak_disimpan_sebagai_teks_biasa(pengguna_uji, koneksi_uji):
    baris = koneksi_uji.execute(
        "SELECT password_hash FROM pengguna WHERE username = %s", ("petugas",)
    ).fetchone()

    assert baris["password_hash"] != "rahasia123"
    assert len(baris["password_hash"]) > 40


def test_username_harus_unik(db):
    from werkzeug.security import generate_password_hash

    from app.models import pengguna as model

    model.buat("kembar", generate_password_hash("a"))

    with pytest.raises(Exception):
        model.buat("kembar", generate_password_hash("b"))
