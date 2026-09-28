"""Akses PostgreSQL memakai psycopg 3. **Tanpa ORM.**

Seluruh query ditulis sebagai SQL mentah dengan parameter (``%s`` atau
``%(nama)s``). Menyusun SQL lewat f-string dari input pengguna dilarang keras.
Query panjang disimpan sebagai berkas ``.sql`` di ``app/sql/`` dan dimuat
lewat :func:`muat_sql`.
"""

import atexit
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator, Sequence

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import Config

DIR_SQL = Path(__file__).resolve().parent / "sql"

_pool: ConnectionPool | None = None


def pool() -> ConnectionPool:
    """Pool koneksi, dibuat saat pertama dibutuhkan.

    Sengaja malas (lazy) supaya modul ini bisa diimpor oleh pengujian yang
    tidak menyentuh database sama sekali.
    """
    global _pool
    if _pool is None:
        Config.periksa()
        _pool = ConnectionPool(
            Config.DATABASE_URL,
            min_size=1,
            max_size=8,
            open=True,
            kwargs={"row_factory": dict_row},
        )
        # Pool menjalankan thread latar. Tanpa penutupan tertib, skrip sekali
        # jalan berakhir dengan PythonFinalizationError saat interpreter mati.
        atexit.register(tutup_pool)
    return _pool


def tutup_pool() -> None:
    """Tutup pool. Dipakai pengujian dan saat aplikasi berhenti."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def koneksi() -> Iterator[Any]:
    """Satu koneksi dari pool. Transaksi otomatis commit bila blok selesai."""
    with pool().connection() as conn:
        yield conn


def ambil_semua(sql: str, params: Sequence | dict | None = None) -> list[dict]:
    with koneksi() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def ambil_satu(sql: str, params: Sequence | dict | None = None) -> dict | None:
    with koneksi() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def jalankan(sql: str, params: Sequence | dict | None = None) -> int:
    """Jalankan perintah tanpa hasil baris. Mengembalikan jumlah baris terpengaruh."""
    with koneksi() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount


@lru_cache(maxsize=None)
def muat_sql(nama: str) -> str:
    """Baca query dari ``app/sql/<nama>``.

    Nama berkas berasal dari kode kita sendiri, bukan dari input pengguna.
    """
    berkas = DIR_SQL / nama
    if not berkas.is_file():
        raise FileNotFoundError(f"Berkas SQL tidak ditemukan: {berkas}")
    return berkas.read_text(encoding="utf-8")
