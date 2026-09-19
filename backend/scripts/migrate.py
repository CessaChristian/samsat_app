#!/usr/bin/env python3
"""Jalankan berkas migrasi ``.sql`` yang belum tercatat di ``schema_migrations``.

Setiap berkas dijalankan dalam satu transaksi tersendiri: bila gagal di
tengah, berkas itu dibatalkan penuh dan migrasi berhenti.

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

DIR_MIGRASI = AKAR_BACKEND / "migrations"


def daftar_migrasi() -> list[Path]:
    """Semua berkas .sql, urut berdasarkan nama (001_, 002_, dst.)."""
    return sorted(DIR_MIGRASI.glob("*.sql"))


def sudah_dijalankan(conn) -> set[str]:
    """Nama migrasi yang tercatat. Kosong bila tabelnya sendiri belum ada."""
    baris = conn.execute(
        "SELECT to_regclass('public.schema_migrations') IS NOT NULL AS ada"
    ).fetchone()
    if not baris[0]:
        return set()
    return {r[0] for r in conn.execute("SELECT nama FROM schema_migrations").fetchall()}


def main(argv: list[str]) -> int:
    Config.periksa()
    hanya_status = "--status" in argv

    berkas_semua = daftar_migrasi()
    if not berkas_semua:
        print(f"Tidak ada berkas migrasi di {DIR_MIGRASI}")
        return 1

    with psycopg.connect(Config.DATABASE_URL, autocommit=True) as conn:
        selesai = sudah_dijalankan(conn)

        if hanya_status:
            print(f"Migrasi di {DIR_MIGRASI}:")
            for berkas in berkas_semua:
                tanda = "sudah" if berkas.name in selesai else "BELUM"
                print(f"  [{tanda}] {berkas.name}")
            return 0

        tertunda = [b for b in berkas_semua if b.name not in selesai]
        if not tertunda:
            print(f"Tidak ada migrasi baru. {len(selesai)} migrasi sudah terpasang.")
            return 0

        for berkas in tertunda:
            isi = berkas.read_text(encoding="utf-8")
            print(f"  menjalankan {berkas.name} ...", end="", flush=True)
            try:
                with conn.transaction():
                    conn.execute(isi)
                    conn.execute(
                        "INSERT INTO schema_migrations (nama) VALUES (%s)",
                        (berkas.name,),
                    )
            except Exception as exc:
                print(" GAGAL")
                print(f"\n{berkas.name} dibatalkan penuh. Penyebab:\n  {exc}")
                return 1
            print(" selesai")

        jumlah = conn.execute("SELECT COUNT(*) FROM dim_wilayah").fetchone()[0]
        print(f"\n{len(tertunda)} migrasi terpasang. dim_wilayah berisi {jumlah} kelurahan.")
        if jumlah != 23:
            print("PERINGATAN: seharusnya 23 kelurahan (lihat spesifikasi bagian 5).")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
