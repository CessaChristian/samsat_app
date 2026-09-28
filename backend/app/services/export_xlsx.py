"""Export Excel.

openpyxl mode write-only: baris dikirim langsung ke berkas dan tidak
ditumpuk di memori, jadi export ribuan baris tetap hemat.
"""

import io

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from app.konstanta import HEADER_WAJIB
from app.models import kewajiban as model_kewajiban
from app.services.export import KOLOM_UANG, PETA_KOLOM, tanggal_stnk

FORMAT_TANGGAL = "DD/MM/YYYY"
FORMAT_UANG = "#,##0"

#: Lebar kolom untuk isi yang panjang. Kolom lain memakai lebar bawaan.
LEBAR_KOLOM: dict[str, int] = {
    "nama": 28,
    "alamat": 38,
    "nm_kecamatan": 16,
    "nm_kelurahan": 20,
    "nm_jenis_kend": 18,
    "nm_merk_kend": 16,
    "tgl_jatuh_tempo_pkb": 13,
    "tgl_jatuh_tempo_stnk": 13,
}

def _sel(lembar, nilai, *, font=None, format_angka=None):
    sel = WriteOnlyCell(lembar, value=nilai)
    if font is not None:
        sel.font = font
    if format_angka is not None:
        sel.number_format = format_angka
    return sel


def _sel_data(lembar, header: str, baris: dict):
    nilai = baris[PETA_KOLOM[header]]

    if header == "tgl_jatuh_tempo_pkb":
        return _sel(lembar, nilai, format_angka=FORMAT_TANGGAL)

    if header == "tgl_jatuh_tempo_stnk":
        tanggal = tanggal_stnk(nilai)
        if tanggal is not None:
            return _sel(lembar, tanggal, format_angka=FORMAT_TANGGAL)
        return nilai

    if header in KOLOM_UANG:
        return _sel(lembar, nilai, format_angka=FORMAT_UANG)

    return nilai


def tulis(saringan) -> io.BytesIO:
    """Susun berkas .xlsx berisi baris yang lolos ``saringan``."""
    buku = Workbook(write_only=True)
    lembar = buku.create_sheet("Rekap PKB")
    lembar.freeze_panes = "A2"

    for urutan, header in enumerate(HEADER_WAJIB, start=1):
        lebar = LEBAR_KOLOM.get(header)
        if lebar is not None:
            lembar.column_dimensions[get_column_letter(urutan)].width = lebar

    tebal = Font(bold=True)
    lembar.append([_sel(lembar, header, font=tebal) for header in HEADER_WAJIB])

    for baris in model_kewajiban.detail(saringan):
        lembar.append([_sel_data(lembar, header, baris) for header in HEADER_WAJIB])

    keluaran = io.BytesIO()
    buku.save(keluaran)
    keluaran.seek(0)
    return keluaran
