"""Akses data tabel ``kewajiban_pkb``. SQL mentah, tanpa ORM."""

from datetime import date
from typing import Iterator, Sequence

from app.database import ambil_satu, koneksi, muat_sql

__all__ = ["detail", "hitung_sudah_ada"]


def hitung_sudah_ada(pasangan: Sequence[tuple[str, date]]) -> int:
    """Berapa banyak (no_polisi, tgl_jatuh_tempo_pkb) yang sudah ada di database.

    Dipakai "Cek File" untuk melaporkan baris baru vs baris diperbarui tanpa
    menulis apa pun. Kunci dikirim sebagai dua array lalu dipasangkan dengan
    ``unnest``, jadi satu query saja berapa pun jumlah barisnya.
    """
    if not pasangan:
        return 0

    baris = ambil_satu(
        """
        SELECT COUNT(*) AS jumlah
          FROM kewajiban_pkb k
          JOIN unnest(%(plat)s::text[], %(tanggal)s::date[]) AS s(no_polisi, tgl)
            ON k.no_polisi = s.no_polisi
           AND k.tgl_jatuh_tempo_pkb = s.tgl
        """,
        {
            "plat": [p for p, _ in pasangan],
            "tanggal": [t for _, t in pasangan],
        },
    )
    return baris["jumlah"]


def detail(saringan) -> Iterator[dict]:
    """Baris detail yang lolos filter, untuk export (bagian 13).

    Memakai kursor sisi server supaya baris mengalir sedikit demi sedikit;
    export tanpa filter bisa berisi ribuan baris dan tidak perlu ditampung
    seluruhnya di memori.

    Koneksi dipegang selama generator dibaca, jadi pemanggil harus
    menghabiskannya (atau menutupnya) sebelum melakukan hal lain ke database.
    """
    with koneksi() as conn, conn.cursor(name="export_detail") as cur:
        cur.itersize = 1000
        cur.execute(muat_sql("export_detail.sql"), saringan.params())
        yield from cur
