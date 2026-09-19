"""Sumber tunggal tanggal "hari ini" untuk seluruh aplikasi.

Seluruh kode yang membutuhkan tanggal hari ini wajib memanggil ``hari_ini()``,
tidak pernah ``date.today()`` langsung. Dengan begitu pengujian dapat
menetapkan tanggal lewat variabel lingkungan ``APP_TODAY``.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 2 dan 7.2.
"""

import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

ZONA = ZoneInfo("Asia/Jakarta")


def hari_ini() -> date:
    """Tanggal hari ini menurut zona waktu Asia/Jakarta.

    Bila ``APP_TODAY`` diisi (format ``YYYY-MM-DD``), nilai itu yang dipakai.
    Berguna untuk pengujian agar angka acuan tetap cocok.
    """
    nilai = (os.environ.get("APP_TODAY") or "").strip()
    if not nilai:
        return datetime.now(ZONA).date()
    try:
        return date.fromisoformat(nilai)
    except ValueError as exc:
        raise ValueError(
            f'APP_TODAY harus berformat YYYY-MM-DD, bukan "{nilai}"'
        ) from exc
