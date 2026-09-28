#!/usr/bin/env python3
"""Jalankan server pengembangan.

Melayani tampilan sekaligus API di satu alamat, asalkan "npm run build"
sudah pernah dijalankan di folder frontend.

    python3 main.py                 # pakai HOST dan PORT dari backend/.env
    python3 main.py --port 5001     # timpa porta sekali jalan
    python3 main.py --tanpa-debug   # matikan muat ulang otomatis
"""

import argparse
import sys
from pathlib import Path

AKAR_BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(AKAR_BACKEND))


def _keluar(pesan: str) -> None:
    print(f"\n{pesan}\n", file=sys.stderr)
    raise SystemExit(1)


try:
    from app import create_app
    from app.config import Config
except ModuleNotFoundError as exc:
    # Penyebab paling sering: dijalankan dengan Python sistem, bukan venv.
    _keluar(
        f"Modul \"{exc.name}\" tidak ditemukan.\n"
        "Kemungkinan virtualenv belum aktif. Coba salah satu:\n\n"
        "    source ../.venv/bin/activate && python3 main.py\n"
        "    ../.venv/bin/python main.py\n\n"
        "Bila virtualenv belum dibuat, lihat README."
    )


def baca_argumen(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Server pengembangan Dashboard PKB Samsat Kota Salatiga.",
    )
    parser.add_argument("--host", help="alamat bind, bawaan dari .env")
    parser.add_argument("--port", type=int, help="porta, bawaan dari .env")
    parser.add_argument(
        "--tanpa-debug",
        action="store_true",
        help="matikan muat ulang otomatis",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    opsi = baca_argumen(argv)

    try:
        Config.periksa()
    except RuntimeError as exc:
        _keluar(str(exc))

    host = opsi.host or Config.HOST
    port = opsi.port or Config.PORT
    debug = False if opsi.tanpa_debug else Config.DEBUG

    app = create_app()

    # Nama database saja yang dicetak; sisanya bisa memuat kata sandi.
    nama_db = Config.DATABASE_URL.rsplit("/", 1)[-1].split("?")[0]

    tampilan_siap = (Config.FOLDER_FRONTEND / "index.html").is_file()

    print()
    print("  Dashboard PKB — Samsat Kota Salatiga")
    print(f"  alamat    http://{host}:{port}")
    print(f"  database  {nama_db}")
    print(f"  tampilan  {'hasil build' if tampilan_siap else 'BELUM DIBANGUN'}")
    print(f"  debug     {'aktif' if debug else 'mati'}")
    print()
    if tampilan_siap:
        print(f"  Buka http://{host}:{port} — tampilan dan API dilayani di sini.")
        print("  Setelah mengubah kode frontend, jalankan 'npm run build' lagi")
        print("  supaya perubahannya ikut tersaji.")
    else:
        print("  Tampilan belum dibangun. Jalankan sekali di folder frontend:")
        print()
        print("      npm install && npm run build")
        print()
        print("  Atau saat sedang mengerjakan tampilan, jalankan 'npm run dev'")
        print("  di terminal lain lalu buka http://localhost:5173")
    print()

    try:
        app.run(host=host, port=port, debug=debug)
    except OSError as exc:
        if getattr(exc, "errno", None) in (48, 98):  # address already in use
            _keluar(
                f"Porta {port} sudah dipakai proses lain.\n"
                "Di macOS, porta 5000 kerap dipakai AirPlay Receiver. Pilihan:\n\n"
                f"    python3 main.py --port 5001\n\n"
                "Bila portanya diganti, sesuaikan juga VITE_API_TARGET pada "
                "frontend/.env."
            )
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
