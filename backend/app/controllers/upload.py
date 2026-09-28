"""Controller unggah: Cek File lalu Simpan.

Cek File memvalidasi tanpa menyentuh tabel data. Bila lolos, berkas dititipkan
ke folder sementara dan tokennya dikembalikan. Simpan mengambil berkas itu,
**memvalidasi ulang dari nol** (hasil pemeriksaan sebelumnya tidak dipercaya),
lalu menyimpan dalam satu transaksi.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 8 dan 11.
"""

import hashlib
import time
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from flask_login import login_required

from app.konstanta import (
    BERKAS_PERNAH_DISIMPAN,
    BERKAS_TERLALU_BESAR,
    BERKAS_TIDAK_TERBACA,
    FORMAT_TIDAK_DIDUKUNG,
)
from app.models import batch as model_batch
from app.models import kewajiban as model_kewajiban
from app.services.berkas_sementara import (
    TokenTidakBerlaku,
    ambil,
    bersihkan_kedaluwarsa,
    buang,
    titipkan,
)
from app.services.pembaca import BerkasTidakTerbaca, baca
from app.services.penyimpan import WilayahTidakDikenal, simpan
from app.services.validator import validasi
from app.views.upload_view import (
    kesalahan_berkas,
    susun_hasil_cek,
    susun_kesalahan,
    susun_peringatan,
    waktu_indonesia,
)

bp = Blueprint("upload", __name__, url_prefix="/api/upload")

# Dua fungsi pembantu
def _folder_sementara() -> Path:
    folder = Path(current_app.config["UPLOAD_TMP_DIR"])
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def _peringatan_berkas_berulang(hash_file: str) -> list[dict]:
    """Pengecekan apakah berkas sudah pernah disimpan atau belum jika iya akan diberitahu"""
    sebelumnya = model_batch.terakhir_dengan_hash(hash_file)
    if not sebelumnya:
        return []
    return [
        {
            "kode": BERKAS_PERNAH_DISIMPAN,
            "pesan": (
                f"Berkas ini sudah pernah disimpan pada "
                f"{waktu_indonesia(sebelumnya['disimpan_pada'])}. "
                "Menyimpan ulang tidak menggandakan data."
            ),
            "baris": [],
        }
    ]

# Endpoint untuk cek file

@bp.post("/check")
@login_required
def check():
    folder = _folder_sementara()
    bersihkan_kedaluwarsa(folder)

    berkas = request.files.get("file")
    if berkas is None or not (berkas.filename or "").strip():
        return (
            jsonify(
                kesalahan_berkas(
                    "BERKAS_TIDAK_ADA", "Tidak ada berkas yang dikirim pada kolom 'file'."
                )
            ),
            400,
        )
    nama = berkas.filename
    akhiran = Path(nama).suffix.lower()
    if akhiran not in current_app.config["EKSTENSI_DIIZINKAN"]:
        return (
            jsonify(
                kesalahan_berkas(
                    FORMAT_TIDAK_DIDUKUNG,
                    f'Format "{akhiran or nama}" tidak didukung. Gunakan .xlsx atau .xls.',
                )
            ),
            400,
        )

    isi = berkas.read()
    batas = current_app.config["MAX_CONTENT_LENGTH"]
    if len(isi) > batas:
        return (
            jsonify(
                kesalahan_berkas(
                    BERKAS_TERLALU_BESAR,
                    f"Berkas melebihi batas {batas // (1024 * 1024)} MB.",
                )
            ),
            400,
        )

    mulai = time.perf_counter()

    # Pengecekan pada file terlebih dahulu jika saat pengecekan gagal, file langsung dibuang
    token = titipkan(
        isi, nama, folder, umur_detik=current_app.config["TOKEN_KEDALUWARSA_DETIK"]
    )

    try:
        terbaca = baca(ambil(token, folder).path)
    except BerkasTidakTerbaca as exc:
        buang(token, folder)
        return jsonify(kesalahan_berkas(BERKAS_TIDAK_TERBACA, str(exc))), 400

    hasil = validasi(terbaca)

    if not hasil.lolos:
        buang(token, folder)
        return jsonify(
            susun_hasil_cek(
                hasil,
                token=None,
                nama_berkas=nama,
                ukuran_byte=len(isi),
                baris_baru=0,
                baris_diperbarui=0,
                waktu_proses_detik=time.perf_counter() - mulai,
            )
        )

    diperbarui = model_kewajiban.hitung_sudah_ada(
        [(b.no_polisi, b.tgl_jatuh_tempo_pkb) for b in hasil.baris]
    )
    hash_file = hashlib.sha256(isi).hexdigest()

    return jsonify(
        susun_hasil_cek(
            hasil,
            token=token,
            nama_berkas=nama,
            ukuran_byte=len(isi),
            baris_baru=len(hasil.baris) - diperbarui,
            baris_diperbarui=diperbarui,
            waktu_proses_detik=time.perf_counter() - mulai,
            peringatan_tambahan=_peringatan_berkas_berulang(hash_file),
        )
    )

# Endpoint simpan data ke database
@bp.post("/commit")
@login_required
def commit():
    folder = _folder_sementara()
    bersihkan_kedaluwarsa(folder)

    muatan = request.get_json(silent=True) or {}
    token = (muatan.get("token") or "").strip()

    try:
        titipan = ambil(token, folder)
    except TokenTidakBerlaku as exc:
        return jsonify(kesalahan_berkas("TOKEN_TIDAK_BERLAKU", str(exc))), 410

    # Validasi sekali lagi
    try:
        terbaca = baca(titipan.path)
    except BerkasTidakTerbaca as exc:
        buang(token, folder)
        return jsonify(kesalahan_berkas(BERKAS_TIDAK_TERBACA, str(exc))), 422

    hasil = validasi(terbaca)
    if not hasil.lolos:
        buang(token, folder)
        return (
            jsonify(
                {
                    "lolos": False,
                    "kesalahan": [susun_kesalahan(k) for k in hasil.kesalahan],
                }
            ),
            422,
        )

    isi = titipan.path.read_bytes()
    try:
        tersimpan = simpan(
            hasil.baris,
            nama_file=titipan.nama_asli,
            hash_file=hashlib.sha256(isi).hexdigest(),
            ukuran_byte=titipan.ukuran_byte,
            peringatan=[susun_peringatan(p) for p in hasil.peringatan],
        )
    except WilayahTidakDikenal as exc:
        buang(token, folder)
        return jsonify(kesalahan_berkas("WILAYAH_TIDAK_DIKENAL", str(exc))), 422

    buang(token, folder)

    return jsonify(
        {
            "batch_id": tersimpan.batch_id,
            "jumlah_baris": tersimpan.jumlah_baris,
            "baris_baru": tersimpan.baris_baru,
            "baris_diperbarui": tersimpan.baris_diperbarui,
        }
    )
