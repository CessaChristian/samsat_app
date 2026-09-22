"""Tes penulis export PDF (bagian 13).

"ReportLab LongTable, kertas A3 landscape, huruf 6–7 pt, header tabel
diulang di setiap halaman, nomor halaman di kaki. Baris judul memuat
'Rekapitulasi PKB — Samsat Kota Salatiga', periode, filter aktif, dan waktu
cetak."
"""

import re
from datetime import date, datetime
from decimal import Decimal

from app.konstanta import HEADER_WAJIB
from app.services.export_pdf import (
    baris_judul,
    baris_tabel,
    lebar_kolom,
    rincian_filter,
    tulis,
)
from app.services.penyimpan import simpan
from app.services.rekap import Filter
from tests.bantu import bersih


def _simpan(baris):
    return simpan(
        baris, nama_file="rekap.xlsx", hash_file="a" * 64, ukuran_byte=1024, peringatan=[]
    )


def _saringan(**ubahan):
    dasar = {"dari": date(2020, 1, 1), "sampai": date(2027, 12, 31)}
    dasar.update(ubahan)
    return Filter(**dasar)


# --- baris judul -----------------------------------------------------------


def test_judul_menyebut_nama_instansi():
    baris = baris_judul(_saringan(), datetime(2026, 9, 22, 17, 30))

    assert baris[0] == "Rekapitulasi PKB — Samsat Kota Salatiga"


def test_judul_menyebut_periode_dengan_tanggal_lengkap():
    baris = baris_judul(
        Filter(dari=date(2026, 1, 1), sampai=date(2026, 9, 22)),
        datetime(2026, 9, 22, 17, 30),
    )

    assert "01/01/2026" in baris[1] and "22/09/2026" in baris[1]


def test_judul_menyebut_waktu_cetak():
    baris = baris_judul(_saringan(), datetime(2026, 9, 22, 17, 30))

    assert "22/09/2026 17:30" in baris[3]


def test_tanpa_filter_disebut_semua_data():
    assert rincian_filter(_saringan()) == "Semua data"


def test_filter_aktif_disebut_satu_per_satu():
    saringan = _saringan(roda=4, lunas=True, kecamatan="TINGKIR")

    assert rincian_filter(saringan) == "Roda 4 · Lunas · Kecamatan TINGKIR"


def test_status_belum_lunas_disebut_apa_adanya():
    assert rincian_filter(_saringan(lunas=False)) == "Belum lunas"


def test_kelurahan_ikut_disebut():
    saringan = _saringan(kecamatan="TINGKIR", kelurahan="TINGKIR LOR")

    assert rincian_filter(saringan) == "Kecamatan TINGKIR · Kelurahan TINGKIR LOR"


# --- isi tabel -------------------------------------------------------------


def test_baris_pertama_adalah_header_21_kolom(db):
    _simpan([bersih()])

    pertama = next(baris_tabel(_saringan()))

    assert pertama == list(HEADER_WAJIB)


def test_uang_dicetak_dengan_pemisah_ribuan_indonesia(db):
    _simpan([bersih(pkb_pokok=Decimal("1234567"))])

    isi = list(baris_tabel(_saringan()))
    kolom = HEADER_WAJIB.index("PKB Pokok")

    assert isi[1][kolom] == "1.234.567"


def test_tanggal_dicetak_dd_mm_yyyy(db):
    _simpan([bersih(tgl_jatuh_tempo_pkb=date(2026, 5, 24))])

    isi = list(baris_tabel(_saringan()))
    kolom = HEADER_WAJIB.index("tgl_jatuh_tempo_pkb")

    assert isi[1][kolom] == "24/05/2026"


def test_sel_kosong_dicetak_sebagai_teks_kosong(db):
    _simpan([bersih(nm_merk_kend=None)])

    isi = list(baris_tabel(_saringan()))
    kolom = HEADER_WAJIB.index("nm_merk_kend")

    assert isi[1][kolom] == ""


def test_hanya_baris_yang_lolos_filter_yang_dicetak(db):
    _simpan(
        [
            bersih(no_polisi="H1111AA", kecamatan="SIDOREJO", kelurahan="SALATIGA"),
            bersih(no_polisi="H2222BB", kecamatan="TINGKIR", kelurahan="TINGKIR LOR"),
        ]
    )

    isi = list(baris_tabel(_saringan(kecamatan="TINGKIR")))

    assert len(isi) == 2  # header + 1 data
    assert isi[1][0] == "H2222BB"


# --- berkas PDF ------------------------------------------------------------


def test_menghasilkan_berkas_pdf(db):
    _simpan([bersih()])

    isi = tulis(_saringan()).getvalue()

    assert isi.startswith(b"%PDF")


def test_kertas_a3_landscape(db):
    """A3 landscape = 1190,55 x 841,89 pt — lebar harus melebihi tinggi."""
    _simpan([bersih()])

    isi = tulis(_saringan()).getvalue()

    cocok = re.search(rb"/MediaBox \[ 0 0 ([\d.]+) ([\d.]+) \]", isi)
    assert cocok, "PDF tidak memuat MediaBox"
    lebar, tinggi = (round(float(n)) for n in cocok.groups())
    assert (lebar, tinggi) == (1191, 842)


def test_pdf_tetap_terbentuk_walau_tidak_ada_baris(db):
    """Filter bisa saja tidak cocok dengan satu baris pun."""
    isi = tulis(_saringan(kecamatan="TINGKIR")).getvalue()

    assert isi.startswith(b"%PDF")


def test_header_tabel_diulang_di_setiap_halaman():
    """Export bisa ratusan halaman; tanpa ini hanya halaman 1 punya header."""
    from app.services.export_pdf import tabel

    assert tabel([list(HEADER_WAJIB)], 1000).repeatRows == 1


def test_lebar_kolom_tidak_melebihi_lebar_kertas():
    # Toleransi 1e-6 pt untuk pembulatan pecahan; itu sepersekian nanometer.
    assert sum(lebar_kolom(1000)) <= 1000 + 1e-6
    assert len(lebar_kolom(1000)) == len(HEADER_WAJIB)


def test_judul_kolom_dipecah_agar_muat_selebar_kolomnya():
    """Judul yang lebih lebar dari kolomnya akan menimpa kolom sebelahnya.

    Lebar isi A3 landscape dengan margin 10 mm = 1133,9 pt.
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth

    from app.services.export_pdf import PADDING, UKURAN_HURUF, pecah_judul

    for header, punya in zip(HEADER_WAJIB, lebar_kolom(1133.9)):
        for baris in pecah_judul(header, punya).split("\n"):
            lebar = stringWidth(baris, "Helvetica-Bold", UKURAN_HURUF)
            assert lebar <= punya - 2 * PADDING, f"{header!r} baris {baris!r} kelebaran"


def test_judul_dipecah_pada_garis_bawah_bila_memungkinkan():
    """Lebih enak dibaca "tgl_jatuh_tempo_" + "pkb" daripada terpotong acak."""
    from app.services.export_pdf import pecah_judul

    assert pecah_judul("tgl_jatuh_tempo_pkb", 60).split("\n") == [
        "tgl_jatuh_tempo_",
        "pkb",
    ]


def test_judul_pendek_tidak_dipecah():
    from app.services.export_pdf import pecah_judul

    assert pecah_judul("TOTAL", 60) == "TOTAL"


def test_tabel_memakai_judul_yang_sudah_dipecah():
    """Tanpa ini, pecah_judul bisa benar tetapi tidak pernah terpakai."""
    from app.services.export_pdf import tabel

    isi = tabel([list(HEADER_WAJIB)], 1133.9)._cellvalues[0]
    panjang = isi[HEADER_WAJIB.index("tgl_jatuh_tempo_stnk")]

    assert "\n" in panjang
    assert panjang.replace("\n", "") == "tgl_jatuh_tempo_stnk"


def test_judul_berspasi_dipecah_pada_spasi_bukan_di_tengah_kata():
    """"PKB Denda Ops" + "en" terbaca salah; pecahnya harus di spasi."""
    from app.services.export_pdf import pecah_judul

    assert pecah_judul("PKB Denda Opsen", 51.5).split("\n") == ["PKB Denda", "Opsen"]


def test_judul_tidak_menyisakan_spasi_di_ujung_baris():
    from app.services.export_pdf import pecah_judul

    for baris in pecah_judul("Denda SWDKLLJ", 51.5).split("\n"):
        assert baris == baris.strip()


def test_isi_sel_yang_kepanjangan_dipecah_agar_tidak_menimpa_kolom_sebelah():
    """Alamat bisa 60+ huruf; satu baris akan meluber ke kolom kecamatan."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    from app.services.export_pdf import HURUF_ISI, PADDING, UKURAN_HURUF, pecah_teks

    alamat = "JL. BIMA NO 7 RT/RW 003/008 KEL. DUKUH KEC. SIDOMUKTI KOTA SALATIGA"
    lebar = lebar_kolom(1133.9)[HEADER_WAJIB.index("alamat")]

    for baris in pecah_teks(alamat, lebar, HURUF_ISI).split("\n"):
        assert stringWidth(baris, HURUF_ISI, UKURAN_HURUF) <= lebar - 2 * PADDING


def test_tabel_memecah_isi_sel_yang_kepanjangan():
    from app.services.export_pdf import tabel

    panjang = "JL. BIMA NO 7 RT/RW 003/008 KEL. DUKUH KEC. SIDOMUKTI KOTA SALATIGA"
    baris = ["-"] * len(HEADER_WAJIB)
    baris[HEADER_WAJIB.index("alamat")] = panjang

    isi = tabel([list(HEADER_WAJIB), baris], 1133.9)._cellvalues[1]
    sel = isi[HEADER_WAJIB.index("alamat")]

    assert "\n" in sel
    assert sel.replace("\n", " ") == panjang


def test_isi_sel_pendek_tidak_diubah():
    from app.services.export_pdf import HURUF_ISI, pecah_teks

    assert pecah_teks("TOYOTA", 60, HURUF_ISI) == "TOYOTA"


def test_nilai_kategori_yang_lazim_muat_satu_baris():
    """Kolom pendek seperti warna sebaiknya tidak pecah di hampir tiap baris.

    Nilai contoh diambil dari isi berkas pusat yang sebenarnya. Kolom teks
    bebas (nama, alamat) memang tetap boleh pecah karena panjangnya
    bermacam-macam.
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth

    from app.services.export_pdf import HURUF_ISI, PADDING, UKURAN_HURUF

    contoh = {
        "nm_kecamatan": "ARGOMULYO",
        "nm_kelurahan": "KUTOWINANGUN LOR",
        "nm_jenis_kend": "MBRG/LIGHT TRUCK",
        "nm_merk_kend": "MITSUBISHI",
        "warna_kend": "SILVER METALIK",
        "warna_tnkb_kend": "HITAM/PUTIH",
    }
    lebar = lebar_kolom(1133.9)

    sempit = [
        kolom
        for kolom, nilai in contoh.items()
        if stringWidth(nilai, HURUF_ISI, UKURAN_HURUF)
        > lebar[HEADER_WAJIB.index(kolom)] - 2 * PADDING
    ]
    assert sempit == []
