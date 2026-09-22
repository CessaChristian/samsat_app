"""Tes penulis export Excel (bagian 13).

"Excel: openpyxl write-only, header tebal, baris header dibekukan."
Isinya 21 kolom persis seperti bagian 4, urutan sama dengan berkas yang
diunggah.
"""

from datetime import date
from decimal import Decimal

from openpyxl import load_workbook

from app.konstanta import HEADER_WAJIB
from app.services.export_xlsx import tulis
from app.services.penyimpan import simpan
from app.services.rekap import Filter
from tests.bantu import bersih


def _simpan(baris):
    return simpan(
        baris, nama_file="rekap.xlsx", hash_file="a" * 64, ukuran_byte=1024, peringatan=[]
    )


def _saringan(**ubahan):
    dasar = {"dari": date(2020, 1, 1), "sampai": date(2027, 12, 31)}
    dasar.update(ubahan)
    return Filter(**dasar)


def _lembar(saringan=None):
    return load_workbook(tulis(saringan or _saringan())).active


def test_header_memuat_21_kolom_sesuai_urutan_berkas_pusat(db):
    _simpan([bersih()])

    lembar = _lembar()

    assert [sel.value for sel in lembar[1]] == list(HEADER_WAJIB)


def test_header_ditulis_tebal(db):
    _simpan([bersih()])

    assert _lembar()["A1"].font.bold is True


def test_baris_header_dibekukan(db):
    _simpan([bersih()])

    assert _lembar().freeze_panes == "A2"


def test_satu_baris_data_per_kewajiban(db):
    _simpan([bersih(no_polisi="H1111AA"), bersih(no_polisi="H2222BB")])

    lembar = _lembar()

    assert lembar.max_row == 3  # 1 header + 2 data


def test_wilayah_memakai_nama_baku_bukan_tulisan_asli_berkas(db):
    """Berkas sumber boleh salah ketik; export menulis nama yang sudah dibakukan."""
    _simpan([bersih(kelurahan="TINGKIR LOR", nm_kelurahan_asli="TINGKR LOR")])

    lembar = _lembar()
    kolom = {nama: i + 1 for i, nama in enumerate(HEADER_WAJIB)}

    assert lembar.cell(row=2, column=kolom["nm_kelurahan"]).value == "TINGKIR LOR"


def test_jatuh_tempo_pkb_ditulis_sebagai_sel_tanggal(db):
    _simpan([bersih(tgl_jatuh_tempo_pkb=date(2026, 5, 24))])

    lembar = _lembar()
    kolom = {nama: i + 1 for i, nama in enumerate(HEADER_WAJIB)}
    sel = lembar.cell(row=2, column=kolom["tgl_jatuh_tempo_pkb"])

    assert sel.value.date() == date(2026, 5, 24)
    assert sel.number_format == "DD/MM/YYYY"


def test_jatuh_tempo_stnk_berbentuk_tanggal_ditulis_sebagai_sel_tanggal(db):
    _simpan([bersih(tgl_jatuh_tempo_stnk="24/05/2030")])

    lembar = _lembar()
    kolom = {nama: i + 1 for i, nama in enumerate(HEADER_WAJIB)}
    sel = lembar.cell(row=2, column=kolom["tgl_jatuh_tempo_stnk"])

    assert sel.value.date() == date(2030, 5, 24)
    assert sel.number_format == "DD/MM/YYYY"


def test_jatuh_tempo_stnk_yang_bukan_tanggal_ditulis_apa_adanya(db):
    """Bagian 4: kolom ini boleh berisi teks aneh dan disimpan apa adanya."""
    _simpan([bersih(tgl_jatuh_tempo_stnk="SEUMUR HIDUP")])

    lembar = _lembar()
    kolom = {nama: i + 1 for i, nama in enumerate(HEADER_WAJIB)}

    assert lembar.cell(row=2, column=kolom["tgl_jatuh_tempo_stnk"]).value == "SEUMUR HIDUP"


def test_kolom_uang_ditulis_sebagai_angka_berformat_ribuan(db):
    _simpan([bersih(pkb_pokok=Decimal("6500"))])

    lembar = _lembar()
    kolom = {nama: i + 1 for i, nama in enumerate(HEADER_WAJIB)}
    sel = lembar.cell(row=2, column=kolom["PKB Pokok"])

    assert sel.value == 6500
    assert sel.number_format == "#,##0"


def test_hanya_baris_yang_lolos_filter_yang_ditulis(db):
    _simpan(
        [
            bersih(no_polisi="H1111AA", kecamatan="SIDOREJO", kelurahan="SALATIGA"),
            bersih(no_polisi="H2222BB", kecamatan="TINGKIR", kelurahan="TINGKIR LOR"),
        ]
    )

    lembar = _lembar(_saringan(kecamatan="TINGKIR"))

    assert lembar.max_row == 2
    assert lembar.cell(row=2, column=1).value == "H2222BB"


def test_kolom_teks_panjang_diberi_lebar_agar_terbaca(db):
    """Alamat bisa puluhan karakter; dengan lebar bawaan isinya terpotong."""
    _simpan([bersih()])

    lembar = _lembar()

    assert lembar.column_dimensions["C"].width >= 30  # kolom "alamat"
