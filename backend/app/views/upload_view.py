"""Penyusun respons JSON untuk endpoint unggah.

Memisahkan bentuk API dari logika validasi: validator menghasilkan objek
Python, berkas ini yang memutuskan seperti apa JSON-nya.
"""

from datetime import date, datetime

from app.services.validator import HasilValidasi, Kesalahan, Peringatan

__all__ = [
    "kesalahan_berkas",
    "susun_kesalahan",
    "susun_hasil_cek",
    "susun_peringatan",
    "waktu_indonesia",
]


def _iso(nilai: date | None) -> str | None:
    return nilai.isoformat() if nilai else None


def waktu_indonesia(saat: datetime) -> str:
    """``18/09/2026 16:12`` — dipakai di pesan peringatan."""
    return saat.strftime("%d/%m/%Y %H:%M")


def susun_kesalahan(kesalahan: Kesalahan) -> dict:
    return {
        "kode": kesalahan.kode,
        "judul": kesalahan.judul,
        "detail": kesalahan.detail,
        "kolom": kesalahan.kolom,
        "baris": kesalahan.baris,
    }


def susun_peringatan(peringatan: Peringatan) -> dict:
    return {
        "kode": peringatan.kode,
        "pesan": peringatan.pesan,
        "baris": peringatan.baris,
    }


def susun_hasil_cek(
    hasil: HasilValidasi,
    *,
    token: str | None,
    nama_berkas: str,
    ukuran_byte: int,
    baris_baru: int,
    baris_diperbarui: int,
    waktu_proses_detik: float,
    peringatan_tambahan: list[dict] | None = None,
) -> dict:
    """Bentuk respons ``POST /api/upload/check``."""
    ringkasan = hasil.ringkasan
    return {
        "lolos": hasil.lolos,
        "token": token,
        "berkas": {"nama": nama_berkas, "ukuran_byte": ukuran_byte},
        "ringkasan": {
            "baris_terbaca": ringkasan.baris_terbaca,
            "rentang_tanggal": {
                "awal": _iso(ringkasan.tanggal_awal),
                "akhir": _iso(ringkasan.tanggal_akhir),
            },
            "kecamatan_ada": ringkasan.kecamatan_ada,
            "kecamatan_master": ringkasan.kecamatan_master,
            "kelurahan_ada": ringkasan.kelurahan_ada,
            "kelurahan_master": ringkasan.kelurahan_master,
            "baris_baru": baris_baru,
            "baris_diperbarui": baris_diperbarui,
            "waktu_proses_detik": round(waktu_proses_detik, 2),
        },
        "peringatan": [susun_peringatan(p) for p in hasil.peringatan]
        + list(peringatan_tambahan or []),
        "kesalahan": [susun_kesalahan(k) for k in hasil.kesalahan],
    }


def kesalahan_berkas(kode: str, pesan: str) -> dict:
    """Kesalahan tingkat berkas, bukan isi."""
    return {"kode": kode, "pesan": pesan}
