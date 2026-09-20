"""Tes untuk app/services/berkas_sementara.py.

Antara "Cek File" dan "Simpan", berkas menunggu di folder sementara dengan
nama token acak dan masa berlaku 30 menit.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 8.
"""

import time

import pytest

from app.services.berkas_sementara import (
    TokenTidakBerlaku,
    ambil,
    bersihkan_kedaluwarsa,
    buang,
    titipkan,
)


@pytest.fixture
def folder(tmp_path):
    return tmp_path / "uploads_tmp"


def test_menitipkan_berkas_menghasilkan_token(folder):
    token = titipkan(b"isi berkas", "rekap.xlsx", folder)

    assert isinstance(token, str)
    assert len(token) >= 20


def test_berkas_dapat_diambil_kembali_dengan_token(folder):
    token = titipkan(b"isi berkas", "rekap.xlsx", folder)

    titipan = ambil(token, folder)

    assert titipan.path.read_bytes() == b"isi berkas"
    assert titipan.nama_asli == "rekap.xlsx"


def test_ukuran_berkas_ikut_tercatat(folder):
    token = titipkan(b"1234567890", "rekap.xlsx", folder)

    assert ambil(token, folder).ukuran_byte == 10


def test_token_tidak_dikenal_ditolak(folder):
    folder.mkdir(parents=True, exist_ok=True)

    with pytest.raises(TokenTidakBerlaku):
        ambil("token-karangan", folder)


def test_token_kedaluwarsa_ditolak(folder):
    token = titipkan(b"isi", "rekap.xlsx", folder, umur_detik=0)
    time.sleep(0.01)

    with pytest.raises(TokenTidakBerlaku):
        ambil(token, folder)


def test_membuang_titipan_menghapus_berkasnya(folder):
    token = titipkan(b"isi", "rekap.xlsx", folder)
    path = ambil(token, folder).path

    buang(token, folder)

    assert not path.exists()
    with pytest.raises(TokenTidakBerlaku):
        ambil(token, folder)


def test_membuang_token_yang_tidak_ada_tidak_menimbulkan_error(folder):
    folder.mkdir(parents=True, exist_ok=True)
    buang("token-karangan", folder)


def test_pembersihan_menghapus_yang_kedaluwarsa_saja(folder):
    lama = titipkan(b"lama", "lama.xlsx", folder, umur_detik=0)
    baru = titipkan(b"baru", "baru.xlsx", folder, umur_detik=1800)
    time.sleep(0.01)

    jumlah = bersihkan_kedaluwarsa(folder)

    assert jumlah == 1
    with pytest.raises(TokenTidakBerlaku):
        ambil(lama, folder)
    assert ambil(baru, folder).nama_asli == "baru.xlsx"


def test_pembersihan_pada_folder_kosong_aman(folder):
    assert bersihkan_kedaluwarsa(folder) == 0


@pytest.mark.parametrize("jahat", ["../../etc/passwd", "a/b", "..", "", "x" * 500])
def test_token_berbentuk_lintasan_ditolak(folder, jahat):
    """Token datang dari klien; jangan pernah dipakai langsung sebagai nama berkas."""
    folder.mkdir(parents=True, exist_ok=True)

    with pytest.raises(TokenTidakBerlaku):
        ambil(jahat, folder)


def test_nama_asli_tidak_memengaruhi_nama_berkas_tersimpan(folder):
    token = titipkan(b"isi", "../../jahat.xlsx", folder)

    titipan = ambil(token, folder)

    assert titipan.path.parent == folder
    assert "jahat" not in titipan.path.name


def test_dua_titipan_menghasilkan_token_berbeda(folder):
    satu = titipkan(b"isi", "a.xlsx", folder)
    dua = titipkan(b"isi", "a.xlsx", folder)

    assert satu != dua
