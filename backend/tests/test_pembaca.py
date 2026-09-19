"""Tes untuk app/services/pembaca.py — membaca berkas Excel apa adanya.

Pembaca tidak menilai isi; ia hanya menyerahkan header dan baris beserta
nomor baris Excel-nya kepada validator.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 4 dan 9 langkah 1.
"""

from datetime import datetime

import pytest

from app.konstanta import HEADER_WAJIB
from app.services.pembaca import BerkasTidakTerbaca, baca
from tests.bantu import baris, tulis_xlsx


def test_membaca_header_dan_satu_baris(tmp_path):
    berkas = tulis_xlsx(tmp_path / "uji.xlsx", [baris()])

    hasil = baca(berkas)

    assert hasil.header == list(HEADER_WAJIB)
    assert len(hasil.baris) == 1


def test_nomor_baris_mengikuti_penomoran_excel(tmp_path):
    """Header adalah baris 1, sehingga data pertama adalah baris 2."""
    berkas = tulis_xlsx(
        tmp_path / "uji.xlsx",
        [baris(no_polisi="H1AA"), baris(no_polisi="H2AA"), baris(no_polisi="H3AA")],
    )

    hasil = baca(berkas)

    assert [b.nomor for b in hasil.baris] == [2, 3, 4]


def test_sel_diambil_berdasarkan_nama_header(tmp_path):
    berkas = tulis_xlsx(tmp_path / "uji.xlsx", [baris(no_polisi="H9999ZZ")])

    hasil = baca(berkas)

    assert hasil.baris[0].sel["no_polisi"] == "H9999ZZ"


def test_sel_tanggal_terbaca_sebagai_datetime(tmp_path):
    berkas = tulis_xlsx(tmp_path / "uji.xlsx", [baris()])

    hasil = baca(berkas)

    assert hasil.baris[0].sel["tgl_jatuh_tempo_pkb"] == datetime(2026, 5, 24)


def test_urutan_kolom_boleh_berbeda(tmp_path):
    terbalik = list(reversed(HEADER_WAJIB))
    berkas = tulis_xlsx(tmp_path / "uji.xlsx", [baris()], header=terbalik)

    hasil = baca(berkas)

    assert hasil.baris[0].sel["no_polisi"] == "H5120GB"
    assert hasil.baris[0].sel["PKB Pokok"] == 6500


def test_kolom_tambahan_bernama_tetap_terbaca_agar_validator_mengabaikannya(tmp_path):
    header = list(HEADER_WAJIB) + ["lokasi_proses"]
    berkas = tulis_xlsx(tmp_path / "uji.xlsx", [baris()], header=header)

    hasil = baca(berkas)

    assert "lokasi_proses" in hasil.header


def test_kolom_tanpa_nama_diabaikan(tmp_path):
    header = list(HEADER_WAJIB) + [None, "   "]
    berkas = tulis_xlsx(tmp_path / "uji.xlsx", [baris()], header=header)

    hasil = baca(berkas)

    assert hasil.header == list(HEADER_WAJIB)


def test_nama_header_dipangkas(tmp_path):
    header = ["  " + nama + " " for nama in HEADER_WAJIB]
    berkas = tulis_xlsx(tmp_path / "uji.xlsx", [baris()], header=header)

    hasil = baca(berkas)

    assert hasil.header == list(HEADER_WAJIB)


def test_baris_hampa_di_akhir_tidak_dihitung_sebagai_data(tmp_path):
    """Excel kerap menyisakan baris kosong; itu bukan baris data."""
    berkas = tulis_xlsx(tmp_path / "uji.xlsx", [baris(), {}, {}])

    hasil = baca(berkas)

    assert len(hasil.baris) == 1


def test_baris_yang_hanya_sebagian_kosong_tetap_dibaca(tmp_path):
    """Baris cacat harus sampai ke validator supaya dilaporkan, bukan dibuang."""
    berkas = tulis_xlsx(tmp_path / "uji.xlsx", [baris(no_polisi=None, nama=None)])

    hasil = baca(berkas)

    assert len(hasil.baris) == 1
    assert hasil.baris[0].sel["no_polisi"] is None


def test_berkas_bukan_excel_ditolak(tmp_path):
    rusak = tmp_path / "rusak.xlsx"
    rusak.write_bytes(b"ini bukan berkas excel")

    with pytest.raises(BerkasTidakTerbaca):
        baca(rusak)


def test_berkas_tidak_ada_ditolak(tmp_path):
    with pytest.raises(BerkasTidakTerbaca):
        baca(tmp_path / "tidak-ada.xlsx")


def test_ekstensi_tidak_didukung_ditolak(tmp_path):
    berkas = tmp_path / "data.csv"
    berkas.write_text("no_polisi\nH1234AB\n", encoding="utf-8")

    with pytest.raises(BerkasTidakTerbaca):
        baca(berkas)


def test_berkas_tanpa_baris_data_menghasilkan_daftar_kosong(tmp_path):
    berkas = tulis_xlsx(tmp_path / "uji.xlsx", [])

    hasil = baca(berkas)

    assert hasil.header == list(HEADER_WAJIB)
    assert hasil.baris == []
