"""Tes untuk endpoint /api/upload/check dan /api/upload/commit.

Alur bagian 8: Cek File memvalidasi tanpa menulis apa pun; Simpan memvalidasi
ulang dari berkas yang dititipkan, lalu menyimpan dalam satu transaksi.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 8 dan 11.
"""

import io

import pytest
from openpyxl import Workbook

from app.konstanta import (
    BERKAS_PERNAH_DISIMPAN,
    DENDA_DIISI_NOL,
    FORMAT_TIDAK_DIDUKUNG,
    HEADER_WAJIB,
    KELURAHAN_TIDAK_DIKENAL,
    RODA_DIUBAH_KE_4,
)
from tests.bantu import baris


def _xlsx(baris_baris, header=None) -> bytes:
    """Berkas .xlsx sebagai bytes, siap dikirim lewat multipart."""
    kolom = list(HEADER_WAJIB if header is None else header)
    wb = Workbook()
    ws = wb.active
    ws.append(kolom)
    for satu in baris_baris:
        ws.append([satu.get(nama) for nama in kolom])
    penampung = io.BytesIO()
    wb.save(penampung)
    return penampung.getvalue()


def _kirim(klien, isi: bytes, nama="rekap.xlsx"):
    return klien.post(
        "/api/upload/check",
        data={"file": (io.BytesIO(isi), nama)},
        content_type="multipart/form-data",
    )


def _hitung(koneksi) -> int:
    return koneksi.execute("SELECT COUNT(*) AS n FROM kewajiban_pkb").fetchone()["n"]


@pytest.fixture
def berkas_baik() -> bytes:
    return _xlsx([baris(no_polisi="H1AA"), baris(no_polisi="H2AA")])


# ---------------------------------------------------------------------------
# Penjagaan sesi
# ---------------------------------------------------------------------------


def test_check_tanpa_sesi_ditolak(klien, berkas_baik):
    assert _kirim(klien, berkas_baik).status_code == 401


def test_commit_tanpa_sesi_ditolak(klien):
    assert klien.post("/api/upload/commit", json={"token": "apa saja"}).status_code == 401


# ---------------------------------------------------------------------------
# Cek File
# ---------------------------------------------------------------------------


def test_berkas_baik_lolos_dan_mendapat_token(klien_masuk, berkas_baik):
    balasan = _kirim(klien_masuk, berkas_baik)
    isi = balasan.get_json()

    assert balasan.status_code == 200
    assert isi["lolos"] is True
    assert isi["token"]
    assert isi["kesalahan"] == []


def test_cek_file_tidak_menulis_ke_database(klien_masuk, berkas_baik, koneksi_uji):
    _kirim(klien_masuk, berkas_baik)

    assert _hitung(koneksi_uji) == 0


def test_ringkasan_memuat_angka_yang_ditampilkan_panel_hijau(klien_masuk, berkas_baik):
    isi = _kirim(klien_masuk, berkas_baik).get_json()
    ringkasan = isi["ringkasan"]

    assert ringkasan["baris_terbaca"] == 2
    assert ringkasan["baris_baru"] == 2
    assert ringkasan["baris_diperbarui"] == 0
    assert ringkasan["kelurahan_master"] == 23
    assert ringkasan["kecamatan_master"] == 4
    assert ringkasan["rentang_tanggal"]["awal"] == "2026-05-24"
    assert "waktu_proses_detik" in ringkasan


def test_nama_dan_ukuran_berkas_dikembalikan(klien_masuk, berkas_baik):
    isi = _kirim(klien_masuk, berkas_baik, nama="rekap-2026-09-18.xlsx").get_json()

    assert isi["berkas"]["nama"] == "rekap-2026-09-18.xlsx"
    assert isi["berkas"]["ukuran_byte"] == len(berkas_baik)


def test_berkas_cacat_ditolak_tanpa_token(klien_masuk):
    isi = _kirim(klien_masuk, _xlsx([baris(nm_kelurahan="TINGKR LOR")])).get_json()

    assert isi["lolos"] is False
    assert isi["token"] is None
    assert isi["kesalahan"][0]["kode"] == KELURAHAN_TIDAK_DIKENAL
    assert isi["kesalahan"][0]["baris"] == [2]


def test_kesalahan_membawa_judul_dan_detail(klien_masuk):
    isi = _kirim(klien_masuk, _xlsx([baris(nm_kelurahan="TINGKR LOR")])).get_json()
    pertama = isi["kesalahan"][0]

    assert "TINGKR LOR" in pertama["judul"]
    assert "TINGKIR LOR" in pertama["detail"]
    assert pertama["kolom"] == "nm_kelurahan"


def test_penyesuaian_otomatis_muncul_sebagai_peringatan(klien_masuk):
    isi = _kirim(klien_masuk, _xlsx([baris(jml_roda=6)])).get_json()

    assert isi["lolos"] is True
    kode = {p["kode"] for p in isi["peringatan"]}
    assert RODA_DIUBAH_KE_4 in kode


def test_denda_kosong_menghasilkan_peringatan(klien_masuk):
    isi = _kirim(klien_masuk, _xlsx([baris(**{"PKB Denda": None})])).get_json()

    assert DENDA_DIISI_NOL in {p["kode"] for p in isi["peringatan"]}


def test_format_tidak_didukung_ditolak(klien_masuk):
    balasan = klien_masuk.post(
        "/api/upload/check",
        data={"file": (io.BytesIO(b"bukan excel"), "data.csv")},
        content_type="multipart/form-data",
    )

    assert balasan.status_code == 400
    assert balasan.get_json()["kode"] == FORMAT_TIDAK_DIDUKUNG


def test_berkas_rusak_ditolak(klien_masuk):
    balasan = _kirim(klien_masuk, b"ini bukan berkas excel sama sekali")

    assert balasan.status_code == 400
    assert balasan.get_json()["kode"] == "BERKAS_TIDAK_TERBACA"


def test_permintaan_tanpa_berkas_ditolak(klien_masuk):
    balasan = klien_masuk.post(
        "/api/upload/check", data={}, content_type="multipart/form-data"
    )

    assert balasan.status_code == 400


# ---------------------------------------------------------------------------
# Simpan
# ---------------------------------------------------------------------------


def test_simpan_dengan_token_menyimpan_baris(klien_masuk, berkas_baik, koneksi_uji):
    token = _kirim(klien_masuk, berkas_baik).get_json()["token"]

    balasan = klien_masuk.post("/api/upload/commit", json={"token": token})
    isi = balasan.get_json()

    assert balasan.status_code == 200
    assert isi["jumlah_baris"] == 2
    assert isi["baris_baru"] == 2
    assert isi["baris_diperbarui"] == 0
    assert isi["batch_id"] > 0
    assert _hitung(koneksi_uji) == 2


def test_token_hanya_berlaku_sekali(klien_masuk, berkas_baik):
    token = _kirim(klien_masuk, berkas_baik).get_json()["token"]
    klien_masuk.post("/api/upload/commit", json={"token": token})

    ulang = klien_masuk.post("/api/upload/commit", json={"token": token})

    assert ulang.status_code == 410


def test_token_karangan_ditolak(klien_masuk):
    balasan = klien_masuk.post("/api/upload/commit", json={"token": "a" * 32})

    assert balasan.status_code == 410


def test_simpan_tanpa_token_ditolak(klien_masuk):
    assert klien_masuk.post("/api/upload/commit", json={}).status_code == 410


def test_unggah_ulang_berkas_sama_memberi_peringatan(klien_masuk, berkas_baik):
    token = _kirim(klien_masuk, berkas_baik).get_json()["token"]
    klien_masuk.post("/api/upload/commit", json={"token": token})

    isi = _kirim(klien_masuk, berkas_baik).get_json()

    assert isi["lolos"] is True
    assert BERKAS_PERNAH_DISIMPAN in {p["kode"] for p in isi["peringatan"]}


def test_unggah_ulang_melaporkan_baris_yang_akan_diperbarui(klien_masuk, berkas_baik):
    token = _kirim(klien_masuk, berkas_baik).get_json()["token"]
    klien_masuk.post("/api/upload/commit", json={"token": token})

    ringkasan = _kirim(klien_masuk, berkas_baik).get_json()["ringkasan"]

    assert ringkasan["baris_baru"] == 0
    assert ringkasan["baris_diperbarui"] == 2


def test_unggah_ulang_tidak_menggandakan_baris(klien_masuk, berkas_baik, koneksi_uji):
    for _ in range(2):
        token = _kirim(klien_masuk, berkas_baik).get_json()["token"]
        klien_masuk.post("/api/upload/commit", json={"token": token})

    assert _hitung(koneksi_uji) == 2


def test_berkas_melebihi_batas_dibalas_json(klien_masuk):
    """Flask menolak badan permintaan yang kelewat besar sebelum view jalan.

    Tanpa penangan khusus, balasannya halaman HTML 413 bawaan Flask yang
    tidak bisa dibaca frontend, sehingga di layar hanya muncul
    "Permintaan gagal (413)" alih-alih keterangan batas ukurannya.
    """
    import io

    besar = b"x" * (11 * 1024 * 1024)

    balasan = klien_masuk.post(
        "/api/upload/check",
        data={"file": (io.BytesIO(besar), "besar.xlsx")},
        content_type="multipart/form-data",
    )

    assert balasan.status_code == 413
    assert balasan.mimetype == "application/json"
    assert balasan.get_json()["kode"] == "BERKAS_TERLALU_BESAR"
    assert "10 MB" in balasan.get_json()["pesan"]
