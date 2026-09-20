"""Akses data tabel ``pengguna``. SQL mentah, tanpa ORM.

Tidak ada pendaftaran mandiri: akun dibuat lewat ``scripts/buat_akun.py``.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 14.
"""

from flask_login import UserMixin

from app.database import ambil_satu, koneksi

__all__ = ["Pengguna", "ambil_per_id", "ambil_per_username", "buat"]


class Pengguna(UserMixin):
    """Pengguna yang sedang bersesi. Hash kata sandi sengaja tidak dibawa."""

    def __init__(self, id: int, username: str) -> None:
        self.id = id
        self.username = username

    @staticmethod
    def dari_baris(baris: dict | None) -> "Pengguna | None":
        if not baris:
            return None
        return Pengguna(id=baris["id"], username=baris["username"])


def ambil_per_id(id_pengguna: int) -> dict | None:
    return ambil_satu(
        "SELECT id, username FROM pengguna WHERE id = %s", (id_pengguna,)
    )


def ambil_per_username(username: str) -> dict | None:
    """Termasuk ``password_hash``; hanya dipakai saat memeriksa login."""
    return ambil_satu(
        "SELECT id, username, password_hash FROM pengguna WHERE username = %s",
        (username,),
    )


def buat(username: str, password_hash: str) -> int:
    """Simpan akun baru. Melempar bila username sudah dipakai."""
    with koneksi() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO pengguna (username, password_hash) VALUES (%s, %s)"
            " RETURNING id",
            (username, password_hash),
        )
        return cur.fetchone()["id"]
