"""Tes untuk app/services/normalisasi.py.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 9.C (normalisasi) dan sebagian
kasus uji bagian 17.2.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app.services.normalisasi import (
    NilaiTidakValid,
    ke_angka,
    ke_tanggal,
    kosong,
    normalkan_plat,
    normalkan_wilayah,
    teks_apa_adanya,
    teks_tanggal_stnk,
)

# --- kosong -----------------------------------------------------------------


@pytest.mark.parametrize("nilai", ["", "   ", "-", "--", " - ", None])
def test_dianggap_kosong(nilai):
    assert kosong(nilai) is True


@pytest.mark.parametrize("nilai", ["0", "H1234AB", "---", 0])
def test_tidak_dianggap_kosong(nilai):
    assert kosong(nilai) is False


# --- plat -------------------------------------------------------------------


def test_plat_huruf_kecil_menjadi_huruf_besar():
    assert normalkan_plat("h1374lk") == "H1374LK"


def test_plat_membuang_spasi():
    assert normalkan_plat("H 1234 AB") == "H1234AB"


def test_plat_membuang_tanda_baca():
    assert normalkan_plat("h-1374/lk.") == "H1374LK"


def test_plat_kosong_menjadi_string_kosong():
    assert normalkan_plat("   ") == ""


# --- wilayah ----------------------------------------------------------------


def test_wilayah_dirapikan_menjadi_huruf_besar():
    assert normalkan_wilayah("  tingkir  lor  ") == "TINGKIR LOR"


def test_wilayah_spasi_ganda_menjadi_satu():
    assert normalkan_wilayah("KAUMAN\t\tKIDUL") == "KAUMAN KIDUL"


# --- angka ------------------------------------------------------------------


def test_angka_dari_sel_numerik_excel():
    assert ke_angka(6500) == Decimal("6500")


def test_angka_float_tidak_kehilangan_presisi():
    assert ke_angka(1234.5) == Decimal("1234.5")


def test_angka_gaya_indonesia_dengan_pemisah_ribuan():
    assert ke_angka("1.234.567") == Decimal("1234567")


def test_angka_gaya_indonesia_dengan_koma_desimal():
    assert ke_angka("1.234,50") == Decimal("1234.50")


def test_angka_kosong_menjadi_none():
    assert ke_angka("") is None
    assert ke_angka("-") is None
    assert ke_angka(None) is None


def test_angka_bukan_bilangan_ditolak():
    with pytest.raises(NilaiTidakValid):
        ke_angka("abc")


def test_angka_negatif_tetap_terbaca_agar_validator_yang_menolak():
    assert ke_angka("-500") == Decimal("-500")


# --- tanggal ----------------------------------------------------------------


def test_tanggal_dari_sel_tanggal_excel():
    assert ke_tanggal(datetime(2026, 5, 24, 0, 0)) == date(2026, 5, 24)


def test_tanggal_dari_objek_date():
    assert ke_tanggal(date(2026, 5, 24)) == date(2026, 5, 24)


def test_tanggal_teks_satu_digit_diterima():
    # Contoh nyata dari berkas instansi.
    assert ke_tanggal("23/2/2027") == date(2027, 2, 23)


def test_tanggal_teks_dua_digit_diterima():
    assert ke_tanggal("24/05/2026") == date(2026, 5, 24)


def test_tanggal_kosong_menjadi_none():
    assert ke_tanggal("") is None
    assert ke_tanggal("--") is None
    assert ke_tanggal(None) is None


def test_tanggal_mustahil_ditolak():
    with pytest.raises(NilaiTidakValid):
        ke_tanggal("31/02/2026")


def test_format_iso_ditolak_karena_bukan_format_instansi():
    with pytest.raises(NilaiTidakValid):
        ke_tanggal("2026-05-24")


def test_angka_mentah_bukan_sel_tanggal_ditolak():
    with pytest.raises(NilaiTidakValid):
        ke_tanggal(46166)


# --- tanggal STNK: disimpan apa adanya --------------------------------------


def test_stnk_sel_tanggal_disimpan_sebagai_dd_mm_yyyy():
    assert teks_tanggal_stnk(datetime(2030, 3, 28)) == "28/03/2030"


def test_stnk_teks_aneh_disimpan_apa_adanya():
    # Contoh nyata dari data instansi; tidak boleh diubah atau ditolak.
    assert teks_tanggal_stnk("28/03/0203") == "28/03/0203"


def test_stnk_kosong_menjadi_string_kosong():
    assert teks_tanggal_stnk(None) == ""


# --- teks lain --------------------------------------------------------------


def test_teks_lain_hanya_dipangkas():
    assert teks_apa_adanya("  TOYOTA  ") == "TOYOTA"


def test_teks_lain_dari_angka_menjadi_teks():
    assert teks_apa_adanya(2018) == "2018"


def test_teks_lain_none_menjadi_string_kosong():
    assert teks_apa_adanya(None) == ""
