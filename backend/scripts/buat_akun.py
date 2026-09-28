#!/usr/bin/env python3
"""Buat akun petugas. Kata sandi diminta lewat getpass, tidak lewat argumen.

Pemakaian:
    python scripts/buat_akun.py <username>
"""

import getpass
import sys
from pathlib import Path

AKAR_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AKAR_BACKEND))

from werkzeug.security import generate_password_hash  # noqa: E402

from app.config import Config  # noqa: E402
from app.models import pengguna as model  # noqa: E402

PANJANG_MINIMAL = 8


def main(argv: list[str]) -> int:
    if len(argv) != 1 or not argv[0].strip():
        print("Pemakaian: python scripts/buat_akun.py <username>")
        return 1

    Config.periksa()
    username = argv[0].strip()

    if model.ambil_per_username(username):
        print(f'Username "{username}" sudah terdaftar.')
        return 1

    sandi = getpass.getpass("Kata sandi        : ")
    if len(sandi) < PANJANG_MINIMAL:
        print(f"Kata sandi minimal {PANJANG_MINIMAL} karakter.")
        return 1
    if sandi != getpass.getpass("Ulangi kata sandi : "):
        print("Kata sandi tidak sama.")
        return 1

    id_baru = model.buat(username, generate_password_hash(sandi))
    print(f'Akun "{username}" dibuat (id {id_baru}).')
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
