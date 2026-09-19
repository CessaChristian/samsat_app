"""Normalisasi nilai sel Excel menjadi tipe Python yang siap divalidasi.

Fungsi di berkas ini **murni**: tidak menyentuh database, tidak membaca
berkas, tidak mencatat log. Semuanya menerima satu nilai sel dan
mengembalikan nilai yang sudah rapi, atau melempar :class:`NilaiTidakValid`
bila isinya tidak bisa dipakai.

Pembagian hasil yang dipakai di seluruh aplikasi:

* sel kosong            -> ``None`` (pemanggil yang memutuskan boleh atau tidak)
* sel berisi tapi salah -> :class:`NilaiTidakValid`
* sel berisi dan benar  -> nilai bertipe ``Decimal`` / ``date`` / ``str``

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 9.C.
"""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.konstanta import TEKS_KOSONG

__all__ = [
    "NilaiTidakValid",
    "ke_angka",
    "ke_tanggal",
    "kosong",
    "normalkan_plat",
    "normalkan_wilayah",
    "teks_apa_adanya",
    "teks_tanggal_stnk",
]


class NilaiTidakValid(ValueError):
    """Sel terisi, tetapi isinya tidak dapat ditafsirkan."""


# Pola ribuan gaya Indonesia: 1.234, 12.345.678 — titik selalu memisah 3 digit.
_POLA_RIBUAN = re.compile(r"-?\d{1,3}(?:\.\d{3})+")
_POLA_TANGGAL = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


def kosong(nilai) -> bool:
    """Apakah sel dianggap kosong.

    Selain sel hampa, teks ``-`` dan ``--`` juga dianggap kosong
    (bagian 9.A). Angka 0 **tidak** kosong.
    """
    if nilai is None:
        return True
    if isinstance(nilai, str):
        return nilai.strip() in TEKS_KOSONG
    return False


def normalkan_plat(nilai) -> str:
    """``h1374LK`` -> ``H1374LK``; ``H 1234 AB`` -> ``H1234AB``."""
    return re.sub(r"[^A-Z0-9]", "", str(nilai or "").upper())


def normalkan_wilayah(nilai) -> str:
    """Pangkas, jadikan huruf besar, dan rapikan spasi ganda menjadi satu."""
    return re.sub(r"\s+", " ", str(nilai or "").upper()).strip()


def ke_angka(nilai) -> Decimal | None:
    """Ubah sel menjadi :class:`Decimal`.

    Menerima angka Excel maupun teks gaya Indonesia (``1.234.567`` dan
    ``1.234,50``). Nilai negatif tetap dikembalikan; penolakannya urusan
    validator (bagian 18.5).
    """
    if kosong(nilai):
        return None
    if isinstance(nilai, bool):
        raise NilaiTidakValid(f'"{nilai}" bukan angka')
    if isinstance(nilai, Decimal):
        return nilai
    if isinstance(nilai, int):
        return Decimal(nilai)
    if isinstance(nilai, float):
        # Lewat str supaya 1234.5 tidak menjadi 1234.5000000000001.
        return Decimal(str(nilai))

    teks = str(nilai).strip()
    if "," in teks:
        # Koma adalah pemisah desimal; titik pasti pemisah ribuan.
        bersih = teks.replace(".", "").replace(",", ".")
    elif _POLA_RIBUAN.fullmatch(teks):
        bersih = teks.replace(".", "")
    else:
        bersih = teks

    try:
        return Decimal(bersih)
    except InvalidOperation as exc:
        raise NilaiTidakValid(f'"{teks}" bukan angka') from exc


def ke_tanggal(nilai) -> date | None:
    """Ubah sel menjadi :class:`datetime.date`.

    Menerima sel tanggal Excel dan teks ``d/m/yyyy`` atau ``dd/mm/yyyy``.
    Format lain — termasuk ``YYYY-MM-DD`` — ditolak karena bukan format
    yang dipakai instansi (bagian 9.A.4b dan kasus uji 17.2).
    """
    if kosong(nilai):
        return None
    if isinstance(nilai, datetime):
        return nilai.date()
    if isinstance(nilai, date):
        return nilai
    if not isinstance(nilai, str):
        raise NilaiTidakValid(f'"{nilai}" bukan sel tanggal')

    teks = nilai.strip()
    cocok = _POLA_TANGGAL.fullmatch(teks)
    if not cocok:
        raise NilaiTidakValid(f'"{teks}" bukan tanggal yang sah')
    hari, bulan, tahun = (int(bagian) for bagian in cocok.groups())
    try:
        return date(tahun, bulan, hari)
    except ValueError as exc:
        raise NilaiTidakValid(f'"{teks}" bukan tanggal yang sah') from exc


def teks_tanggal_stnk(nilai) -> str:
    """Jatuh tempo STNK disimpan sebagai teks, apa adanya.

    Sel tanggal ditulis ``dd/mm/yyyy``; isi lain — termasuk teks aneh seperti
    ``28/03/0203`` yang muncul di data asli — disimpan tanpa diubah
    (bagian 4 dan 9.C).
    """
    if nilai is None:
        return ""
    if isinstance(nilai, (datetime, date)):
        return f"{nilai.day:02d}/{nilai.month:02d}/{nilai.year:04d}"
    return str(nilai).strip()


def teks_apa_adanya(nilai) -> str:
    """Kolom teks yang tidak divalidasi: cukup dipangkas.

    Angka bulat yang terbaca sebagai float (``2018.0``) ditulis tanpa
    ekor desimal supaya ``th_buat`` tidak berubah bentuk.
    """
    if nilai is None:
        return ""
    if isinstance(nilai, float) and nilai.is_integer():
        return str(int(nilai))
    return str(nilai).strip()
