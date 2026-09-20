"""Akses data tabel ``kewajiban_pkb``. SQL mentah, tanpa ORM."""

from datetime import date
from typing import Sequence

from app.database import ambil_satu

__all__ = ["hitung_sudah_ada"]


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
