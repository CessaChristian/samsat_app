"""Tes untuk app/services/penyimpan.py — menyimpan satu berkas dalam satu transaksi.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 6 (cara pembaruan), 7.1 (status
lunas), dan 10.3 (langkah simpan).

Seluruh tes di berkas ini memakai database uji yang ditunjuk
``TEST_DATABASE_URL`` dan dikosongkan sebelum setiap tes.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.services.penyimpan import WilayahTidakDikenal, simpan
from tests.bantu import bersih


def _hitung(koneksi) -> int:
    return koneksi.execute("SELECT COUNT(*) AS n FROM kewajiban_pkb").fetchone()["n"]


def _ambil(koneksi, plat: str, tanggal: date) -> dict:
    return koneksi.execute(
        "SELECT * FROM kewajiban_pkb WHERE no_polisi = %s AND tgl_jatuh_tempo_pkb = %s",
        (plat, tanggal),
    ).fetchone()


def _simpan(baris, nama_file="rekap.xlsx", hash_file="a" * 64, peringatan=None):
    return simpan(
        baris,
        nama_file=nama_file,
        hash_file=hash_file,
        ukuran_byte=1024,
        peringatan=peringatan or [],
    )


# ---------------------------------------------------------------------------
# Menyimpan baris baru
# ---------------------------------------------------------------------------


def test_menyimpan_satu_baris(db, koneksi_uji):
    _simpan([bersih()])

    assert _hitung(koneksi_uji) == 1


def test_nilai_tersimpan_utuh(db, koneksi_uji):
    _simpan([bersih()])

    satu = _ambil(koneksi_uji, "H5120GB", date(2026, 5, 24))
    assert satu["pkb_pokok"] == Decimal("6500.00")
    assert satu["swdkllj"] == Decimal("35000.00")
    assert satu["jml_roda"] == 4
    assert satu["nama"] == "RUSIYATI"
    assert satu["tgl_jatuh_tempo_stnk"] == "24/05/2030"


def test_wilayah_dipetakan_ke_dim_wilayah(db, koneksi_uji):
    _simpan([bersih()])

    satu = koneksi_uji.execute(
        "SELECT w.kecamatan, w.kelurahan FROM kewajiban_pkb k"
        " JOIN dim_wilayah w ON w.id = k.wilayah_id"
    ).fetchone()
    assert satu["kecamatan"] == "TINGKIR"
    assert satu["kelurahan"] == "KUTOWINANGUN LOR"


def test_hasil_melaporkan_jumlah_baris_baru(db):
    hasil = _simpan([bersih(no_polisi="H1AA"), bersih(no_polisi="H2AA")])

    assert hasil.jumlah_baris == 2
    assert hasil.baris_baru == 2
    assert hasil.baris_diperbarui == 0


def test_batch_tercatat(db, koneksi_uji):
    hasil = _simpan([bersih()], nama_file="rekap-2026-09-18.xlsx")

    batch = koneksi_uji.execute(
        "SELECT * FROM ingest_batch WHERE id = %s", (hasil.batch_id,)
    ).fetchone()
    assert batch["nama_file"] == "rekap-2026-09-18.xlsx"
    assert batch["jumlah_baris"] == 1
    assert batch["baris_baru"] == 1


def test_peringatan_ikut_tersimpan_di_batch(db, koneksi_uji):
    peringatan = [{"kode": "DENDA_DIISI_NOL", "pesan": "3 sel denda/PNBP kosong diisi 0"}]
    hasil = _simpan([bersih()], peringatan=peringatan)

    batch = koneksi_uji.execute(
        "SELECT peringatan FROM ingest_batch WHERE id = %s", (hasil.batch_id,)
    ).fetchone()
    assert batch["peringatan"] == peringatan


# ---------------------------------------------------------------------------
# Pembaruan: kunci (no_polisi, tgl_jatuh_tempo_pkb)
# ---------------------------------------------------------------------------


def test_kunci_sama_memperbarui_bukan_menambah(db, koneksi_uji):
    _simpan([bersih(pkb_denda=Decimal("50000"))])
    _simpan([bersih(pkb_denda=Decimal("75000"))])

    assert _hitung(koneksi_uji) == 1
    satu = _ambil(koneksi_uji, "H5120GB", date(2026, 5, 24))
    assert satu["pkb_denda"] == Decimal("75000.00")


def test_pembaruan_dilaporkan_sebagai_diperbarui(db):
    _simpan([bersih()])
    hasil = _simpan([bersih()])

    assert hasil.baris_baru == 0
    assert hasil.baris_diperbarui == 1


def test_jatuh_tempo_baru_menambah_baris_dan_baris_lama_tetap(db, koneksi_uji):
    _simpan([bersih(tgl_jatuh_tempo_pkb=date(2025, 9, 18))])
    _simpan([bersih(tgl_jatuh_tempo_pkb=date(2026, 9, 18))])

    assert _hitung(koneksi_uji) == 2
    assert _ambil(koneksi_uji, "H5120GB", date(2025, 9, 18)) is not None


def test_plat_yang_tidak_muncul_lagi_tidak_dihapus(db, koneksi_uji):
    _simpan([bersih(no_polisi="H1AA"), bersih(no_polisi="H2AA")])
    _simpan([bersih(no_polisi="H1AA")])

    assert _hitung(koneksi_uji) == 2
    assert _ambil(koneksi_uji, "H2AA", date(2026, 5, 24)) is not None


def test_pertama_terlihat_tidak_berubah_saat_diperbarui(db, koneksi_uji):
    _simpan([bersih()])
    awal = _ambil(koneksi_uji, "H5120GB", date(2026, 5, 24))

    _simpan([bersih(pkb_denda=Decimal("99999"))])
    sesudah = _ambil(koneksi_uji, "H5120GB", date(2026, 5, 24))

    assert sesudah["pertama_terlihat"] == awal["pertama_terlihat"]
    assert sesudah["terakhir_diperbarui"] > awal["terakhir_diperbarui"]


def test_batch_id_menunjuk_batch_terakhir(db, koneksi_uji):
    _simpan([bersih()])
    kedua = _simpan([bersih()])

    satu = _ambil(koneksi_uji, "H5120GB", date(2026, 5, 24))
    assert satu["batch_id"] == kedua.batch_id


# ---------------------------------------------------------------------------
# Status lunas (bagian 7.1)
# ---------------------------------------------------------------------------


def test_satu_baris_berarti_belum_lunas(db, koneksi_uji):
    _simpan([bersih()])

    assert _ambil(koneksi_uji, "H5120GB", date(2026, 5, 24))["lunas"] is False


def test_baris_terbaru_belum_lunas_dan_yang_lama_lunas(db, koneksi_uji):
    _simpan(
        [
            bersih(tgl_jatuh_tempo_pkb=date(2025, 5, 24)),
            bersih(tgl_jatuh_tempo_pkb=date(2026, 5, 24)),
        ]
    )

    assert _ambil(koneksi_uji, "H5120GB", date(2025, 5, 24))["lunas"] is True
    assert _ambil(koneksi_uji, "H5120GB", date(2026, 5, 24))["lunas"] is False


def test_jatuh_tempo_baru_mengubah_status_baris_lama_menjadi_lunas(db, koneksi_uji):
    """Pembayaran terlihat dari munculnya jatuh tempo tahun berikutnya."""
    _simpan([bersih(tgl_jatuh_tempo_pkb=date(2025, 5, 24))])
    assert _ambil(koneksi_uji, "H5120GB", date(2025, 5, 24))["lunas"] is False

    _simpan([bersih(tgl_jatuh_tempo_pkb=date(2026, 5, 24))])

    assert _ambil(koneksi_uji, "H5120GB", date(2025, 5, 24))["lunas"] is True
    assert _ambil(koneksi_uji, "H5120GB", date(2026, 5, 24))["lunas"] is False


def test_status_plat_lain_tidak_ikut_dihitung_ulang(db, koneksi_uji):
    _simpan(
        [
            bersih(no_polisi="H1AA", tgl_jatuh_tempo_pkb=date(2025, 5, 24)),
            bersih(no_polisi="H1AA", tgl_jatuh_tempo_pkb=date(2026, 5, 24)),
        ]
    )
    _simpan([bersih(no_polisi="H2AA")])

    assert _ambil(koneksi_uji, "H1AA", date(2025, 5, 24))["lunas"] is True
    assert _ambil(koneksi_uji, "H1AA", date(2026, 5, 24))["lunas"] is False


# ---------------------------------------------------------------------------
# Transaksi
# ---------------------------------------------------------------------------


def test_kelurahan_tidak_dikenal_membatalkan_seluruh_penyimpanan(db, koneksi_uji):
    _simpan([bersih(no_polisi="H1AA")])

    with pytest.raises(WilayahTidakDikenal):
        _simpan(
            [
                bersih(no_polisi="H2AA"),
                bersih(no_polisi="H3AA", kelurahan="TIDAK ADA", kecamatan="TINGKIR"),
            ]
        )

    assert _hitung(koneksi_uji) == 1


def test_kegagalan_tidak_meninggalkan_batch(db, koneksi_uji):
    with pytest.raises(WilayahTidakDikenal):
        _simpan([bersih(kelurahan="TIDAK ADA")])

    jumlah = koneksi_uji.execute("SELECT COUNT(*) AS n FROM ingest_batch").fetchone()["n"]
    assert jumlah == 0


def test_daftar_kosong_ditolak(db):
    with pytest.raises(ValueError):
        _simpan([])


# ---------------------------------------------------------------------------
# Riwayat batch
# ---------------------------------------------------------------------------


def test_hash_sama_boleh_disimpan_dua_kali(db, koneksi_uji):
    _simpan([bersih()], hash_file="b" * 64)
    _simpan([bersih()], hash_file="b" * 64)

    jumlah = koneksi_uji.execute("SELECT COUNT(*) AS n FROM ingest_batch").fetchone()["n"]
    assert jumlah == 2
    assert _hitung(koneksi_uji) == 1
