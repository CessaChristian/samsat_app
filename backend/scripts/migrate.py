#!/usr/bin/env python3
"""Pasang migrasi database yang belum terpasang.

Pemakaian:
    python scripts/migrate.py            # jalankan yang belum dijalankan
    python scripts/migrate.py --status   # tampilkan status saja

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 10.1.
"""

import sys
from pathlib import Path

AKAR_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AKAR_BACKEND))

import psycopg  # noqa: E402

from app.config import Config  # noqa: E402
from app.utils.migrasi import (  # noqa: E402
    DIR_MIGRASI,
    daftar_migrasi,
    jalankan_migrasi,
    sudah_dijalankan,
)


def cetak_status() -> int:
    with psycopg.connect(Config.DATABASE_URL, autocommit=True) as conn:
        selesai = sudah_dijalankan(conn)
    print(f"Migrasi di {DIR_MIGRASI}:")
    for berkas in daftar_migrasi():
        tanda = "sudah" if berkas.name in selesai else "BELUM"
        print(f"  [{tanda}] {berkas.name}")
    return 0


def main(argv: list[str]) -> int:
    Config.periksa()

    if "--status" in argv:
        return cetak_status()

    try:
        terpasang = jalankan_migrasi(Config.DATABASE_URL, lapor=print)
    except RuntimeError as exc:
        print(f"\nGAGAL: {exc}")
        return 1

    if not terpasang:
        print("Tidak ada migrasi baru.")
    else:
        print(f"\n{len(terpasang)} migrasi terpasang: {', '.join(terpasang)}")

    with psycopg.connect(Config.DATABASE_URL) as conn:
        jumlah = conn.execute("SELECT COUNT(*) FROM dim_wilayah").fetchone()[0]
    print(f"dim_wilayah berisi {jumlah} kelurahan.")
    if jumlah != 23:
        print("PERINGATAN: seharusnya 23 kelurahan (lihat spesifikasi bagian 5).")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
