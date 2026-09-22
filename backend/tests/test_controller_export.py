"""Tes controller /api/export.xlsx dan /api/export.pdf (bagian 11 dan 13).

Nama berkas: ``rekap-pkb_<dari>_<sampai>.xlsx`` / ``.pdf``.
"""

import io
from datetime import date

from openpyxl import load_workbook

from app.services.penyimpan import simpan
from tests.bantu import bersih

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _simpan(baris):
    return simpan(
        baris, nama_file="rekap.xlsx", hash_file="a" * 64, ukuran_byte=1024, peringatan=[]
    )


RENTANG = "dari=2020-01-01&sampai=2026-06-30"


# --- akses -----------------------------------------------------------------


def test_export_excel_menolak_tamu(klien):
    assert klien.get("/api/export.xlsx").status_code == 401


def test_export_pdf_menolak_tamu(klien):
    assert klien.get("/api/export.pdf").status_code == 401


# --- excel -----------------------------------------------------------------


def test_export_excel_mengirim_berkas_xlsx(klien_masuk):
    _simpan([bersih()])

    balasan = klien_masuk.get(f"/api/export.xlsx?{RENTANG}")

    assert balasan.status_code == 200
    assert balasan.mimetype == XLSX


def test_nama_berkas_excel_memuat_periode(klien_masuk):
    _simpan([bersih()])

    balasan = klien_masuk.get(f"/api/export.xlsx?{RENTANG}")

    assert "rekap-pkb_2020-01-01_2026-06-30.xlsx" in balasan.headers["Content-Disposition"]


def test_isi_excel_berisi_baris_yang_tersimpan(klien_masuk):
    _simpan([bersih(no_polisi="H1111AA"), bersih(no_polisi="H2222BB")])

    balasan = klien_masuk.get(f"/api/export.xlsx?{RENTANG}")
    lembar = load_workbook(io.BytesIO(balasan.data)).active

    assert lembar.max_row == 3
    assert [lembar.cell(row=r, column=1).value for r in (2, 3)] == ["H1111AA", "H2222BB"]


# --- pdf -------------------------------------------------------------------


def test_export_pdf_mengirim_berkas_pdf(klien_masuk):
    _simpan([bersih()])

    balasan = klien_masuk.get(f"/api/export.pdf?{RENTANG}")

    assert balasan.status_code == 200
    assert balasan.mimetype == "application/pdf"
    assert balasan.data.startswith(b"%PDF")


def test_nama_berkas_pdf_memuat_periode(klien_masuk):
    _simpan([bersih()])

    balasan = klien_masuk.get(f"/api/export.pdf?{RENTANG}")

    assert "rekap-pkb_2020-01-01_2026-06-30.pdf" in balasan.headers["Content-Disposition"]


# --- filter ----------------------------------------------------------------


def test_export_mengikuti_filter_yang_dikirim(klien_masuk):
    _simpan(
        [
            bersih(no_polisi="H1111AA", kecamatan="SIDOREJO", kelurahan="SALATIGA"),
            bersih(no_polisi="H2222BB", kecamatan="TINGKIR", kelurahan="TINGKIR LOR"),
        ]
    )

    balasan = klien_masuk.get(f"/api/export.xlsx?{RENTANG}&kecamatan=TINGKIR")
    lembar = load_workbook(io.BytesIO(balasan.data)).active

    assert lembar.max_row == 2
    assert lembar.cell(row=2, column=1).value == "H2222BB"


def test_filter_tidak_masuk_akal_ditolak(klien_masuk):
    balasan = klien_masuk.get("/api/export.xlsx?roda=3")

    assert balasan.status_code == 400
    assert balasan.get_json()["kode"] == "FILTER_TIDAK_VALID"


# --- keamanan --------------------------------------------------------------


def test_berkas_export_tidak_boleh_disimpan_cache(klien_masuk):
    """Isinya nama dan alamat pemilik kendaraan."""
    _simpan([bersih()])

    balasan = klien_masuk.get(f"/api/export.xlsx?{RENTANG}")

    assert balasan.headers["Cache-Control"] == "no-store"


def test_nama_berkas_memakai_batas_hari_ini_bukan_tanggal_yang_diminta(
    klien_masuk, monkeypatch
):
    """Bagian 11: "sampai" yang melewati hari ini dipotong menjadi hari ini."""
    monkeypatch.setenv("APP_TODAY", "2026-09-19")
    _simpan([bersih()])

    balasan = klien_masuk.get("/api/export.xlsx?dari=2020-01-01&sampai=2027-12-31")

    assert "rekap-pkb_2020-01-01_2026-09-19.xlsx" in balasan.headers["Content-Disposition"]
