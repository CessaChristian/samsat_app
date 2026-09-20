"""Tes integrasi: berkas contoh nyata dibaca, divalidasi, lalu disimpan.

Ini kriteria selesai Tahap 3 pada SPESIFIKASI_DASHBOARD_PKB.md bagian 16,
diuji terhadap angka acuan bagian 17.1.

Berkas contoh tidak ikut repositori (berisi data pribadi), jadi seluruh tes di
sini dilewati bila ``samples/data_dummy_bersih.xlsx`` tidak ada.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.config import AKAR_PROYEK
from app.services.pembaca import baca
from app.services.penyimpan import simpan
from app.services.validator import validasi

BERKAS_CONTOH = AKAR_PROYEK / "samples" / "data_dummy_bersih.xlsx"

pytestmark = pytest.mark.skipif(
    not BERKAS_CONTOH.is_file(),
    reason=f"berkas contoh tidak tersedia di {BERKAS_CONTOH}",
)

HARI_ACUAN = date(2026, 9, 19)


@pytest.fixture
def tersimpan(db):
    """Berkas contoh yang sudah divalidasi dan disimpan sekali."""
    hasil = validasi(baca(BERKAS_CONTOH))
    assert hasil.lolos, f"berkas contoh seharusnya lolos: {hasil.kesalahan[:3]}"
    return simpan(
        hasil.baris,
        nama_file=BERKAS_CONTOH.name,
        hash_file="c" * 64,
        ukuran_byte=BERKAS_CONTOH.stat().st_size,
    )


def _angka(koneksi, sql: str, params=None):
    return koneksi.execute(sql, params).fetchone()


def test_berkas_contoh_lolos_validasi():
    hasil = validasi(baca(BERKAS_CONTOH))

    assert hasil.lolos is True
    assert hasil.kesalahan == []
    assert hasil.ringkasan.baris_terbaca == 4822


def test_seluruh_baris_tersimpan(tersimpan, koneksi_uji):
    assert tersimpan.jumlah_baris == 4822
    assert tersimpan.baris_baru == 4822
    assert tersimpan.baris_diperbarui == 0
    assert _angka(koneksi_uji, "SELECT COUNT(*) AS n FROM kewajiban_pkb")["n"] == 4822


def test_jumlah_plat_unik(tersimpan, koneksi_uji):
    hasil = _angka(koneksi_uji, "SELECT COUNT(DISTINCT no_polisi) AS n FROM kewajiban_pkb")
    assert hasil["n"] == 4816


def test_rentang_jatuh_tempo(tersimpan, koneksi_uji):
    hasil = _angka(
        koneksi_uji,
        "SELECT MIN(tgl_jatuh_tempo_pkb) AS awal, MAX(tgl_jatuh_tempo_pkb) AS akhir"
        " FROM kewajiban_pkb",
    )
    assert hasil["awal"] == date(2021, 1, 2)
    assert hasil["akhir"] == date(2028, 2, 27)


def test_jumlah_baris_lunas(tersimpan, koneksi_uji):
    hasil = _angka(koneksi_uji, "SELECT COUNT(*) AS n FROM kewajiban_pkb WHERE lunas")
    assert hasil["n"] == 6


def test_pembagian_baris_tampil_dan_penanda(tersimpan, koneksi_uji):
    hasil = _angka(
        koneksi_uji,
        "SELECT COUNT(*) FILTER (WHERE tgl_jatuh_tempo_pkb <= %s) AS tampil,"
        "       COUNT(*) FILTER (WHERE tgl_jatuh_tempo_pkb >  %s) AS penanda"
        "  FROM kewajiban_pkb",
        (HARI_ACUAN, HARI_ACUAN),
    )
    assert hasil["tampil"] == 4645
    assert hasil["penanda"] == 177


def test_angka_kartu_sesuai_acuan(tersimpan, koneksi_uji):
    hasil = _angka(
        koneksi_uji,
        "SELECT COUNT(*) AS objek,"
        "       SUM(pkb_pokok + pkb_denda)       AS pkb,"
        "       SUM(pkb_opsen + pkb_denda_opsen) AS opsen_pkb,"
        "       SUM(swdkllj + denda_swdkllj)     AS swdkllj"
        "  FROM kewajiban_pkb WHERE tgl_jatuh_tempo_pkb <= %s",
        (HARI_ACUAN,),
    )
    assert hasil["objek"] == 4645
    assert hasil["pkb"] == Decimal("8859350800")
    assert hasil["opsen_pkb"] == Decimal("3430740400")
    assert hasil["swdkllj"] == Decimal("1494891000")


def test_komposisi_roda_sesuai_acuan(tersimpan, koneksi_uji):
    hasil = _angka(
        koneksi_uji,
        "SELECT COUNT(*) FILTER (WHERE jml_roda = 4) AS roda4,"
        "       COUNT(*) FILTER (WHERE jml_roda = 2) AS roda2"
        "  FROM kewajiban_pkb WHERE tgl_jatuh_tempo_pkb <= %s",
        (HARI_ACUAN,),
    )
    assert hasil["roda4"] == 4117
    assert hasil["roda2"] == 528


def test_pkb_per_kecamatan_sesuai_acuan(tersimpan, koneksi_uji):
    baris = koneksi_uji.execute(
        "SELECT w.kecamatan, COALESCE(SUM(k.pkb_pokok + k.pkb_denda), 0) AS pkb"
        "  FROM dim_wilayah w"
        "  LEFT JOIN kewajiban_pkb k"
        "    ON k.wilayah_id = w.id AND k.tgl_jatuh_tempo_pkb <= %s"
        " GROUP BY w.kecamatan ORDER BY pkb DESC",
        (HARI_ACUAN,),
    ).fetchall()

    assert {b["kecamatan"]: b["pkb"] for b in baris} == {
        "SIDOREJO": Decimal("6211792200"),
        "ARGOMULYO": Decimal("1600389500"),
        "TINGKIR": Decimal("1047169100"),
        "SIDOMUKTI": Decimal("0"),
    }


def test_kelurahan_yang_berisi_data(tersimpan, koneksi_uji):
    hasil = _angka(
        koneksi_uji,
        "SELECT COUNT(DISTINCT wilayah_id) AS n FROM kewajiban_pkb"
        " WHERE tgl_jatuh_tempo_pkb <= %s",
        (HARI_ACUAN,),
    )
    assert hasil["n"] == 19


# ---------------------------------------------------------------------------
# Unggah ulang berkas yang sama
# ---------------------------------------------------------------------------


def test_unggah_ulang_tidak_menggandakan_baris(tersimpan, koneksi_uji):
    hasil = validasi(baca(BERKAS_CONTOH))
    kedua = simpan(
        hasil.baris,
        nama_file=BERKAS_CONTOH.name,
        hash_file="c" * 64,
        ukuran_byte=BERKAS_CONTOH.stat().st_size,
    )

    assert kedua.baris_baru == 0
    assert kedua.baris_diperbarui == 4822
    assert _angka(koneksi_uji, "SELECT COUNT(*) AS n FROM kewajiban_pkb")["n"] == 4822


def test_unggah_ulang_mencatat_batch_kedua(tersimpan, koneksi_uji):
    hasil = validasi(baca(BERKAS_CONTOH))
    simpan(
        hasil.baris,
        nama_file=BERKAS_CONTOH.name,
        hash_file="c" * 64,
        ukuran_byte=BERKAS_CONTOH.stat().st_size,
    )

    assert _angka(koneksi_uji, "SELECT COUNT(*) AS n FROM ingest_batch")["n"] == 2
