"""Tes penyajian tampilan oleh Flask.

Satu perintah ``python3 main.py`` harus melayani tampilan sekaligus API di
alamat yang sama, supaya saat demo tidak perlu menyalakan dua service.
"""

import pytest

from app.config import AKAR_PROYEK, Config

DIST = AKAR_PROYEK / "frontend" / "dist"

butuh_build = pytest.mark.skipif(
    not (DIST / "index.html").is_file(),
    reason="frontend/dist belum dibangun (jalankan npm run build)",
)


@butuh_build
def test_akar_mengirim_halaman_tampilan(klien):
    balasan = klien.get("/")

    assert balasan.status_code == 200
    assert balasan.mimetype == "text/html"
    assert b'<div id="root">' in balasan.data


@butuh_build
def test_berkas_aset_tersaji(klien):
    nama = next(p.name for p in (DIST / "assets").iterdir() if p.suffix == ".css")

    balasan = klien.get(f"/assets/{nama}")

    assert balasan.status_code == 200
    assert balasan.mimetype == "text/css"


def test_api_tidak_tertimpa_penyajian_berkas(klien):
    """Penjaga: rute API harus tetap menang atas penyajian berkas statis."""
    balasan = klien.get("/api/rekap")

    assert balasan.status_code == 401
    assert balasan.mimetype == "application/json"


def test_jalur_api_yang_tidak_ada_tetap_404(klien):
    assert klien.get("/api/jalur-ngawur").status_code == 404


def test_pesan_jelas_bila_tampilan_belum_dibangun(db, tmp_path):
    """Saat demo, layar putih tanpa keterangan jauh lebih buruk daripada pesan."""
    from app import create_app

    class ConfigTanpaBuild(Config):
        FOLDER_FRONTEND = tmp_path / "belum-ada"

    balasan = create_app(ConfigTanpaBuild).test_client().get("/")

    assert balasan.status_code == 503
    assert "npm run build" in balasan.get_data(as_text=True)
