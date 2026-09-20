"""Menampung berkas unggahan antara "Cek File" dan "Simpan".

Berkas yang lolos pemeriksaan dititipkan ke folder sementara dengan nama
token acak, berlaku 30 menit. Klien hanya memegang tokennya.

Token datang dari klien, jadi **tidak pernah** dipakai langsung sebagai nama
berkas: bentuknya diperiksa dulu agar tidak bisa menunjuk ke luar folder.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 8.
"""

import json
import re
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "Titipan",
    "TokenTidakBerlaku",
    "ambil",
    "bersihkan_kedaluwarsa",
    "buang",
    "titipkan",
]

#: Bentuk token yang sah: hasil secrets.token_urlsafe, tanpa pemisah lintasan.
_POLA_TOKEN = re.compile(r"\A[A-Za-z0-9_-]{16,64}\Z")

_AKHIRAN_DIIZINKAN = (".xlsx", ".xls")
_AKHIRAN_LAIN = ".bin"

UMUR_BAWAAN_DETIK = 30 * 60


class TokenTidakBerlaku(Exception):
    """Token tidak dikenal, sudah kedaluwarsa, atau bentuknya mencurigakan."""


@dataclass(frozen=True)
class Titipan:
    token: str
    path: Path
    nama_asli: str
    ukuran_byte: int


def _periksa_token(token: str) -> str:
    if not isinstance(token, str) or not _POLA_TOKEN.match(token):
        raise TokenTidakBerlaku("Token tidak berlaku.")
    return token


def _path_meta(token: str, folder: Path) -> Path:
    return folder / f"{token}.json"


def titipkan(
    data: bytes,
    nama_asli: str,
    folder: Path,
    umur_detik: int = UMUR_BAWAAN_DETIK,
) -> str:
    """Simpan berkas dan kembalikan tokennya."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    token = secrets.token_urlsafe(24)
    # Hanya ekstensinya yang diambil dari nama asli; sisanya diabaikan supaya
    # nama kiriman tidak pernah menentukan lokasi berkas.
    akhiran = Path(nama_asli).suffix.lower()
    if akhiran not in _AKHIRAN_DIIZINKAN:
        akhiran = _AKHIRAN_LAIN

    path_data = folder / f"{token}{akhiran}"
    path_data.write_bytes(data)

    _path_meta(token, folder).write_text(
        json.dumps(
            {
                "nama_asli": nama_asli,
                "berkas": path_data.name,
                "ukuran_byte": len(data),
                "kedaluwarsa": time.time() + umur_detik,
            }
        ),
        encoding="utf-8",
    )
    return token


def ambil(token: str, folder: Path) -> Titipan:
    """Ambil titipan yang masih berlaku. Melempar bila tidak ada atau lewat waktu."""
    token = _periksa_token(token)
    folder = Path(folder)
    path_meta = _path_meta(token, folder)

    if not path_meta.is_file():
        raise TokenTidakBerlaku("Token tidak dikenal atau sudah dipakai.")

    try:
        meta = json.loads(path_meta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        buang(token, folder)
        raise TokenTidakBerlaku("Titipan rusak.") from exc

    if time.time() > meta.get("kedaluwarsa", 0):
        buang(token, folder)
        raise TokenTidakBerlaku("Token sudah kedaluwarsa. Jalankan Cek File lagi.")

    path_data = folder / meta["berkas"]
    if not path_data.is_file():
        buang(token, folder)
        raise TokenTidakBerlaku("Berkas titipan tidak ditemukan.")

    return Titipan(
        token=token,
        path=path_data,
        nama_asli=meta.get("nama_asli", ""),
        ukuran_byte=meta.get("ukuran_byte", path_data.stat().st_size),
    )


def buang(token: str, folder: Path) -> None:
    """Hapus titipan. Aman dipanggil untuk token yang sudah tidak ada."""
    try:
        token = _periksa_token(token)
    except TokenTidakBerlaku:
        return

    folder = Path(folder)
    path_meta = _path_meta(token, folder)
    if path_meta.is_file():
        try:
            meta = json.loads(path_meta.read_text(encoding="utf-8"))
            (folder / meta["berkas"]).unlink(missing_ok=True)
        except (json.JSONDecodeError, OSError, KeyError):
            pass
        path_meta.unlink(missing_ok=True)

    # Jaga-jaga bila metadata sudah hilang lebih dulu.
    for akhiran in (*_AKHIRAN_DIIZINKAN, _AKHIRAN_LAIN):
        (folder / f"{token}{akhiran}").unlink(missing_ok=True)


def bersihkan_kedaluwarsa(folder: Path) -> int:
    """Buang seluruh titipan yang sudah lewat waktu. Kembalikan jumlahnya."""
    folder = Path(folder)
    if not folder.is_dir():
        return 0

    sekarang = time.time()
    jumlah = 0
    for path_meta in folder.glob("*.json"):
        try:
            meta = json.loads(path_meta.read_text(encoding="utf-8"))
            masih_berlaku = sekarang <= meta.get("kedaluwarsa", 0)
        except (json.JSONDecodeError, OSError):
            masih_berlaku = False
        if not masih_berlaku:
            buang(path_meta.stem, folder)
            jumlah += 1
    return jumlah
