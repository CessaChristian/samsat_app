"""Menjalankan berkas migrasi ``.sql`` yang belum tercatat.

Dipakai oleh ``scripts/migrate.py`` dan oleh fixture pengujian yang perlu
menyiapkan skema pada database uji. Setiap berkas dijalankan dalam satu
transaksi tersendiri.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 10.1.
"""

from pathlib import Path
from typing import Callable

import psycopg

DIR_MIGRASI = Path(__file__).resolve().parent.parent.parent / "migrations"

__all__ = ["DIR_MIGRASI", "daftar_migrasi", "jalankan_migrasi", "sudah_dijalankan"]


def daftar_migrasi(dir_migrasi: Path | None = None) -> list[Path]:
    """Semua berkas .sql, urut berdasarkan nama (001_, 002_, dst.)."""
    return sorted((dir_migrasi or DIR_MIGRASI).glob("*.sql"))


def sudah_dijalankan(conn) -> set[str]:
    """Nama migrasi yang tercatat. Kosong bila tabelnya sendiri belum ada."""
    baris = conn.execute(
        "SELECT to_regclass('public.schema_migrations') IS NOT NULL AS ada"
    ).fetchone()
    if not baris[0]:
        return set()
    return {r[0] for r in conn.execute("SELECT nama FROM schema_migrations").fetchall()}


def jalankan_migrasi(
    url: str,
    dir_migrasi: Path | None = None,
    lapor: Callable[[str], None] | None = None,
) -> list[str]:
    """Pasang migrasi yang belum terpasang. Kembalikan nama yang baru dijalankan.

    Melempar :class:`RuntimeError` bila sebuah migrasi gagal; migrasi itu
    dibatalkan penuh dan sisanya tidak dijalankan.
    """
    berkas_semua = daftar_migrasi(dir_migrasi)
    if not berkas_semua:
        raise RuntimeError(f"Tidak ada berkas migrasi di {dir_migrasi or DIR_MIGRASI}")

    terpasang: list[str] = []
    with psycopg.connect(url, autocommit=True) as conn:
        selesai = sudah_dijalankan(conn)
        for berkas in berkas_semua:
            if berkas.name in selesai:
                continue
            if lapor:
                lapor(f"  menjalankan {berkas.name} ...")
            try:
                with conn.transaction():
                    conn.execute(berkas.read_text(encoding="utf-8"))
                    conn.execute(
                        "INSERT INTO schema_migrations (nama) VALUES (%s)",
                        (berkas.name,),
                    )
            except Exception as exc:
                raise RuntimeError(
                    f"{berkas.name} gagal dan dibatalkan penuh. Penyebab: {exc}"
                ) from exc
            terpasang.append(berkas.name)
    return terpasang
