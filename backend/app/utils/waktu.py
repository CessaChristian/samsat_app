"""Sumber tunggal tanggal "hari ini" untuk seluruh aplikasi.

Seluruh kode yang membutuhkan tanggal hari ini wajib memanggil ``hari_ini()``,
tidak pernah ``date.today()`` langsung, supaya zona waktunya seragam.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

ZONA = ZoneInfo("Asia/Jakarta")


def hari_ini() -> date:
    """Tanggal hari ini menurut zona waktu Asia/Jakarta."""
    return datetime.now(ZONA).date()
