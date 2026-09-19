"""Tes untuk app/konstanta.py — master wilayah dan daftar header berkas pusat.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 4 (21 header) dan bagian 5
(4 kecamatan, 23 kelurahan).
"""

import re
from pathlib import Path

from app.konstanta import (
    HEADER_WAJIB,
    KECAMATAN,
    KELURAHAN_KE_KECAMATAN,
    KOLOM_DENDA_BOLEH_KOSONG,
    KOLOM_NILAI_INTI,
)

BERKAS_SEED = Path(__file__).resolve().parent.parent / "migrations" / "002_seed_wilayah.sql"


def test_master_berisi_23_kelurahan():
    assert len(KELURAHAN_KE_KECAMATAN) == 23


def test_master_berisi_4_kecamatan():
    assert KECAMATAN == ("ARGOMULYO", "SIDOMUKTI", "SIDOREJO", "TINGKIR")


def test_sidorejo_kidul_berada_di_kecamatan_tingkir():
    # Jebakan yang ditandai spesifikasi bagian 5.
    assert KELURAHAN_KE_KECAMATAN["SIDOREJO KIDUL"] == "TINGKIR"


def test_salatiga_adalah_kelurahan_di_kecamatan_sidorejo():
    assert KELURAHAN_KE_KECAMATAN["SALATIGA"] == "SIDOREJO"


def test_jumlah_kelurahan_tiap_kecamatan():
    hitung: dict[str, int] = {}
    for kecamatan in KELURAHAN_KE_KECAMATAN.values():
        hitung[kecamatan] = hitung.get(kecamatan, 0) + 1
    assert hitung == {
        "ARGOMULYO": 6,
        "SIDOMUKTI": 4,
        "SIDOREJO": 6,
        "TINGKIR": 7,
    }


def test_header_wajib_berjumlah_21():
    assert len(HEADER_WAJIB) == 21


def test_header_wajib_persis_dan_urut_seperti_berkas_pusat():
    assert HEADER_WAJIB == (
        "no_polisi",
        "nama",
        "alamat",
        "nm_kecamatan",
        "nm_kelurahan",
        "nm_jenis_kend",
        "nm_merk_kend",
        "th_buat",
        "warna_kend",
        "warna_tnkb_kend",
        "jml_roda",
        "tgl_jatuh_tempo_pkb",
        "tgl_jatuh_tempo_stnk",
        "PKB Pokok",
        "PKB Denda",
        "PKB Opsen",
        "PKB Denda Opsen",
        "SWDKLLJ",
        "Denda SWDKLLJ",
        "PNBP",
        "TOTAL",
    )


def test_kolom_nilai_inti_adalah_tiga_kolom_yang_wajib_terisi():
    assert KOLOM_NILAI_INTI == ("PKB Pokok", "PKB Opsen", "SWDKLLJ")


def test_kolom_denda_boleh_kosong_diisi_nol():
    assert KOLOM_DENDA_BOLEH_KOSONG == (
        "PKB Denda",
        "PKB Denda Opsen",
        "Denda SWDKLLJ",
        "PNBP",
    )


def test_seed_sql_cocok_dengan_master_di_kode():
    """Migrasi 002 dan konstanta tidak boleh menyimpang satu sama lain."""
    isi = BERKAS_SEED.read_text(encoding="utf-8")
    pasangan = set(re.findall(r"\('([A-Z ]+)', '([A-Z ]+)'\)", isi))
    dari_kode = {(kec, kel) for kel, kec in KELURAHAN_KE_KECAMATAN.items()}
    assert pasangan == dari_kode
