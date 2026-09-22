"""Tes integrasi Tahap 8: unggah berkas contoh lalu export.

Kriteria selesai bagian 16: "Export tanpa filter berisi 4.645 baris x 21
kolom (APP_TODAY=2026-09-19)".
"""

import io
import re

import pytest
from openpyxl import load_workbook

from app.config import AKAR_PROYEK
from app.konstanta import HEADER_WAJIB

BERKAS_CONTOH = AKAR_PROYEK / "samples" / "data_dummy_bersih.xlsx"

pytestmark = pytest.mark.skipif(
    not BERKAS_CONTOH.is_file(),
    reason=f"berkas contoh tidak tersedia di {BERKAS_CONTOH}",
)

HARI_ACUAN = "2026-09-19"
BARIS_ACUAN = 4645


@pytest.fixture(autouse=True)
def tanggal_tetap(monkeypatch):
    monkeypatch.setenv("APP_TODAY", HARI_ACUAN)


@pytest.fixture
def dashboard_terisi(klien_masuk):
    isi = BERKAS_CONTOH.read_bytes()
    cek = klien_masuk.post(
        "/api/upload/check",
        data={"file": (io.BytesIO(isi), BERKAS_CONTOH.name)},
        content_type="multipart/form-data",
    ).get_json()
    assert cek["lolos"] is True, cek["kesalahan"][:3]

    simpan = klien_masuk.post("/api/upload/commit", json={"token": cek["token"]})
    assert simpan.status_code == 200
    return klien_masuk


def test_export_excel_tanpa_filter_berisi_4645_baris_dan_21_kolom(dashboard_terisi):
    balasan = dashboard_terisi.get("/api/export.xlsx")

    lembar = load_workbook(io.BytesIO(balasan.data)).active

    assert lembar.max_column == len(HEADER_WAJIB) == 21
    assert lembar.max_row == BARIS_ACUAN + 1  # ditambah baris header


def test_export_pdf_tanpa_filter_memuat_jumlah_baris_yang_sama(dashboard_terisi):
    from app.services.export_pdf import baris_tabel
    from app.services.rekap import buat_filter

    isi = list(baris_tabel(buat_filter({})))

    assert len(isi) == BARIS_ACUAN + 1


def test_export_pdf_tanpa_filter_menjadi_berkas_banyak_halaman(dashboard_terisi):
    balasan = dashboard_terisi.get("/api/export.pdf")

    assert balasan.data.startswith(b"%PDF")
    halaman = len(re.findall(rb"/Type\s*/Page[^s]", balasan.data))
    assert halaman > 20, f"hanya {halaman} halaman"


def test_jumlah_baris_export_sama_dengan_kartu_objek_di_dashboard(dashboard_terisi):
    """Uji silang: rekap dan export memakai query berbeda untuk filter sama.

    Bila keduanya pernah berbeda, angka di layar tidak lagi menggambarkan isi
    berkas yang diunduh petugas.
    """
    for kueri in ("", "?kecamatan=SIDOREJO", "?roda=2", "?status=BELUM_LUNAS"):
        objek = dashboard_terisi.get(f"/api/rekap{kueri}").get_json()["kpi"]["objek"]
        lembar = load_workbook(
            io.BytesIO(dashboard_terisi.get(f"/api/export.xlsx{kueri}").data)
        ).active

        assert lembar.max_row == objek + 1, f"tidak cocok pada filter {kueri!r}"


def test_jumlah_pkb_di_export_sama_dengan_angka_acuan(dashboard_terisi):
    """Angka acuan bagian 17.1: kartu PKB tanpa filter Rp 8.859.350.800.

    PKB = pkb_pokok + pkb_denda, dua kolom yang ikut ditulis di export.
    """
    lembar = load_workbook(io.BytesIO(dashboard_terisi.get("/api/export.xlsx").data)).active
    pokok = HEADER_WAJIB.index("PKB Pokok") + 1
    denda = HEADER_WAJIB.index("PKB Denda") + 1

    jumlah = sum(
        lembar.cell(row=r, column=pokok).value + lembar.cell(row=r, column=denda).value
        for r in range(2, lembar.max_row + 1)
    )

    assert jumlah == 8_859_350_800
