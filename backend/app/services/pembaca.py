"""Membaca berkas Excel dari pusat menjadi header + baris bernomor.

Pembaca sengaja **tidak menilai isi**. Sel diserahkan apa adanya kepada
validator; satu-satunya keputusan yang diambil di sini adalah kolom mana yang
punya nama dan baris mana yang benar-benar hampa.

Nomor baris yang dibawa adalah nomor baris Excel: header adalah baris 1,
sehingga data pertama adalah baris 2. Nomor itulah yang muncul di pesan
kesalahan.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = ["BarisMentah", "BerkasExcel", "BerkasTidakTerbaca", "baca"]


class BerkasTidakTerbaca(Exception):
    """Berkas tidak dapat dibuka atau bukan berkas Excel yang sah."""


@dataclass(frozen=True)
class BarisMentah:
    """Satu baris data beserta nomor barisnya di Excel."""

    nomor: int
    sel: dict[str, Any]


@dataclass(frozen=True)
class BerkasExcel:
    """Isi lembar pertama: nama kolom dan seluruh baris datanya."""

    header: list[str] = field(default_factory=list)
    baris: list[BarisMentah] = field(default_factory=list)


def _peta_kolom(header_mentah) -> dict[int, str]:
    """Indeks kolom -> nama header, setelah dipangkas.

    Kolom tanpa nama diabaikan. Nama yang muncul dua kali hanya diambil yang
    pertama, supaya satu nama selalu menunjuk satu kolom.
    """
    peta: dict[int, str] = {}
    sudah: set[str] = set()
    for indeks, nilai in enumerate(header_mentah or ()):
        nama = str(nilai).strip() if nilai is not None else ""
        if not nama or nama in sudah:
            continue
        peta[indeks] = nama
        sudah.add(nama)
    return peta


def _hampa(nilai_nilai) -> bool:
    """Baris yang seluruh selnya hampa bukanlah baris data."""
    for nilai in nilai_nilai:
        if nilai is None:
            continue
        if isinstance(nilai, str) and not nilai.strip():
            continue
        return False
    return True


def _rakit(peta: dict[int, str], nilai_nilai) -> dict[str, Any]:
    panjang = len(nilai_nilai)
    return {
        nama: (nilai_nilai[indeks] if indeks < panjang else None)
        for indeks, nama in peta.items()
    }


def _baca_xlsx(path: Path) -> BerkasExcel:
    from openpyxl import load_workbook

    buku = load_workbook(path, data_only=True, read_only=True)
    try:
        lembar = buku.worksheets[0]
        baris_iter = lembar.iter_rows(values_only=True)
        peta = _peta_kolom(next(baris_iter, None))

        data: list[BarisMentah] = []
        for nomor, nilai_nilai in enumerate(baris_iter, start=2):
            if _hampa(nilai_nilai):
                continue
            data.append(BarisMentah(nomor=nomor, sel=_rakit(peta, nilai_nilai)))
        return BerkasExcel(header=list(peta.values()), baris=data)
    finally:
        buku.close()


def _baca_xls(path: Path) -> BerkasExcel:
    import xlrd

    buku = xlrd.open_workbook(str(path))
    lembar = buku.sheet_by_index(0)

    def nilai_sel(baris_ke: int, kolom_ke: int):
        sel = lembar.cell(baris_ke, kolom_ke)
        if sel.ctype == xlrd.XL_CELL_DATE:
            return xlrd.xldate_as_datetime(sel.value, buku.datemode)
        if sel.ctype == xlrd.XL_CELL_EMPTY:
            return None
        return sel.value

    if lembar.nrows == 0:
        return BerkasExcel()

    peta = _peta_kolom([nilai_sel(0, k) for k in range(lembar.ncols)])

    data: list[BarisMentah] = []
    for baris_ke in range(1, lembar.nrows):
        nilai_nilai = [nilai_sel(baris_ke, k) for k in range(lembar.ncols)]
        if _hampa(nilai_nilai):
            continue
        data.append(BarisMentah(nomor=baris_ke + 1, sel=_rakit(peta, nilai_nilai)))
    return BerkasExcel(header=list(peta.values()), baris=data)


def baca(path: str | Path) -> BerkasExcel:
    """Baca lembar pertama berkas ``.xlsx`` atau ``.xls``.

    Melempar :class:`BerkasTidakTerbaca` bila berkas hilang, bukan Excel,
    atau rusak.
    """
    path = Path(path)
    if not path.is_file():
        raise BerkasTidakTerbaca(f"Berkas tidak ditemukan: {path.name}")

    akhiran = path.suffix.lower()
    if akhiran == ".xlsx":
        pembaca = _baca_xlsx
    elif akhiran == ".xls":
        pembaca = _baca_xls
    else:
        raise BerkasTidakTerbaca(
            f'Format "{akhiran or path.name}" tidak didukung. Gunakan .xlsx atau .xls.'
        )

    try:
        return pembaca(path)
    except BerkasTidakTerbaca:
        raise
    except Exception as exc:
        raise BerkasTidakTerbaca(
            f"Berkas {path.name} tidak dapat dibaca sebagai Excel: {exc}"
        ) from exc
