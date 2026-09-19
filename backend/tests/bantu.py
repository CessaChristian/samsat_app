"""Pembantu pengujian: membuat berkas Excel kecil di folder sementara.

Kasus uji bagian 17.2 meminta berkas uji dibuat **secara terprogram**, bukan
disimpan sebagai berkas contoh, supaya tidak ada data pribadi di repositori.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

from openpyxl import Workbook

from app.konstanta import HEADER_WAJIB

#: Satu baris yang lolos seluruh pemeriksaan, dipakai sebagai titik awal.
#: Urutan nilainya mengikuti HEADER_WAJIB.
BARIS_BAIK: dict[str, Any] = {
    "no_polisi": "H5120GB",
    "nama": "RUSIYATI",
    "alamat": "JL TIRTOYOSO I/09 RT07/IX SLTG",
    "nm_kecamatan": "TINGKIR",
    "nm_kelurahan": "KUTOWINANGUN LOR",
    "nm_jenis_kend": "MPNP/MINIBUS",
    "nm_merk_kend": "TOYOTA",
    "th_buat": 2018,
    "warna_kend": "PUTIH",
    "warna_tnkb_kend": "PUTIH",
    "jml_roda": 4,
    "tgl_jatuh_tempo_pkb": datetime(2026, 5, 24),
    "tgl_jatuh_tempo_stnk": datetime(2030, 5, 24),
    "PKB Pokok": 6500,
    "PKB Denda": 500,
    "PKB Opsen": 4500,
    "PKB Denda Opsen": 500,
    "SWDKLLJ": 35000,
    "Denda SWDKLLJ": 8000,
    "PNBP": 0,
    "TOTAL": 55000,
}


def baris(**ubahan: Any) -> dict[str, Any]:
    """Satu baris baik, dengan kolom tertentu diubah.

    Contoh: ``baris(nm_kelurahan="TINGKR LOR")``.
    """
    hasil = dict(BARIS_BAIK)
    hasil.update(ubahan)
    return hasil


def tulis_xlsx(
    path: Path,
    baris_baris: Iterable[dict[str, Any]],
    header: Sequence[str] | None = None,
) -> Path:
    """Tulis berkas .xlsx dengan header lalu baris data.

    ``header`` bawaannya adalah ke-21 header wajib. Berikan daftar lain untuk
    menguji header yang hilang, berlebih, atau berbeda urutan.
    """
    kolom = list(HEADER_WAJIB if header is None else header)
    wb = Workbook()
    ws = wb.active
    ws.append(kolom)
    for satu in baris_baris:
        ws.append([satu.get(nama) for nama in kolom])
    wb.save(path)
    return path
