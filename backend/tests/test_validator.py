"""Tes untuk app/services/validator.py.

Mencakup seluruh tabel kasus uji SPESIFIKASI_DASHBOARD_PKB.md bagian 17.2,
ditambah aturan bagian 9.A (menolak), 9.B (penyesuaian otomatis), dan
pengelompokan kesalahan.

Validator harus **murni**: tidak menyentuh database.
"""

from datetime import date, datetime
from decimal import Decimal

from app.konstanta import (
    BARIS_KEMBAR,
    DENDA_DIISI_NOL,
    HEADER_KOLOM_HILANG,
    KECAMATAN_TIDAK_DIKENAL,
    KELURAHAN_TIDAK_DIKENAL,
    NILAI_DENDA_TIDAK_VALID,
    NILAI_INTI_KOSONG,
    NILAI_INTI_TIDAK_VALID,
    PASANGAN_WILAYAH_SALAH,
    PLAT_KOSONG,
    RODA_DIUBAH_KE_2,
    RODA_DIUBAH_KE_4,
    RODA_TIDAK_VALID,
    TANGGAL_KOSONG,
    TANGGAL_TIDAK_VALID,
)
from app.konstanta import HEADER_WAJIB
from app.services.pembaca import BarisMentah, BerkasExcel
from app.services.validator import validasi
from tests.bantu import baris


def _berkas(*baris_baris, header=None) -> BerkasExcel:
    """Rakit BerkasExcel langsung, tanpa singgah ke disk."""
    kolom = list(HEADER_WAJIB if header is None else header)
    return BerkasExcel(
        header=kolom,
        baris=[
            BarisMentah(nomor=nomor, sel={k: satu.get(k) for k in kolom})
            for nomor, satu in enumerate(baris_baris, start=2)
        ],
    )


def _kode(hasil) -> set[str]:
    return {k.kode for k in hasil.kesalahan}


def _kode_peringatan(hasil) -> set[str]:
    return {p.kode for p in hasil.peringatan}


def _cari(hasil, kode):
    return [k for k in hasil.kesalahan if k.kode == kode]


# ---------------------------------------------------------------------------
# Jalur bahagia
# ---------------------------------------------------------------------------


def test_berkas_baik_lolos_tanpa_kesalahan():
    hasil = validasi(_berkas(baris()))

    assert hasil.lolos is True
    assert hasil.kesalahan == []
    assert len(hasil.baris) == 1


def test_berkas_baik_menghasilkan_baris_siap_simpan():
    hasil = validasi(_berkas(baris()))
    satu = hasil.baris[0]

    assert satu.no_polisi == "H5120GB"
    assert satu.tgl_jatuh_tempo_pkb == date(2026, 5, 24)
    assert satu.kecamatan == "TINGKIR"
    assert satu.kelurahan == "KUTOWINANGUN LOR"
    assert satu.jml_roda == 4
    assert satu.pkb_pokok == Decimal("6500")
    assert satu.swdkllj == Decimal("35000")


def test_kolom_export_disimpan_apa_adanya():
    hasil = validasi(_berkas(baris(nm_merk_kend="  TOYOTA  ", th_buat=2018)))
    satu = hasil.baris[0]

    assert satu.nm_merk_kend == "TOYOTA"
    assert satu.th_buat == "2018"
    assert satu.nm_kecamatan_asli == "TINGKIR"


# ---------------------------------------------------------------------------
# A.1 — tahap header
# ---------------------------------------------------------------------------


def test_satu_header_hilang_ditolak():
    kurang = [h for h in HEADER_WAJIB if h != "PKB Opsen"]
    hasil = validasi(_berkas(baris(), header=kurang))

    assert hasil.lolos is False
    assert _kode(hasil) == {HEADER_KOLOM_HILANG}


def test_header_hilang_menghentikan_pemeriksaan_isi():
    """Bagian 9 langkah 2: kolom lain tidak bisa dibaca, jadi jangan dilaporkan."""
    kurang = [h for h in HEADER_WAJIB if h != "PKB Opsen"]
    rusak = baris(no_polisi="", jml_roda="abc", nm_kelurahan="TIDAK ADA")

    hasil = validasi(_berkas(rusak, header=kurang))

    assert _kode(hasil) == {HEADER_KOLOM_HILANG}


def test_pesan_header_menyebut_nama_kolom_yang_hilang():
    kurang = [h for h in HEADER_WAJIB if h != "PKB Opsen"]
    hasil = validasi(_berkas(baris(), header=kurang))

    assert 'PKB Opsen' in _cari(hasil, HEADER_KOLOM_HILANG)[0].judul


def test_beberapa_header_hilang_dilaporkan_semua():
    kurang = [h for h in HEADER_WAJIB if h not in ("PKB Opsen", "SWDKLLJ")]
    hasil = validasi(_berkas(baris(), header=kurang))

    gabungan = " ".join(k.judul for k in _cari(hasil, HEADER_KOLOM_HILANG))
    assert "PKB Opsen" in gabungan
    assert "SWDKLLJ" in gabungan


def test_urutan_header_bebas():
    hasil = validasi(_berkas(baris(), header=list(reversed(HEADER_WAJIB))))

    assert hasil.lolos is True


def test_kolom_tambahan_diabaikan():
    tambahan = list(HEADER_WAJIB) + ["lokasi_proses"]
    hasil = validasi(_berkas(baris(), header=tambahan))

    assert hasil.lolos is True


# ---------------------------------------------------------------------------
# A.2 — wilayah
# ---------------------------------------------------------------------------


def test_kelurahan_salah_eja_ditolak_dengan_saran():
    hasil = validasi(_berkas(baris(nm_kelurahan="TINGKR LOR")))

    assert hasil.lolos is False
    assert KELURAHAN_TIDAK_DIKENAL in _kode(hasil)
    assert "TINGKIR LOR" in _cari(hasil, KELURAHAN_TIDAK_DIKENAL)[0].detail


def test_nama_kecamatan_dipakai_sebagai_kelurahan_ditolak():
    """ARGOMULYO adalah kecamatan, bukan kelurahan (kasus uji 17.2)."""
    hasil = validasi(_berkas(baris(nm_kelurahan="ARGOMULYO")))

    assert hasil.lolos is False
    assert KELURAHAN_TIDAK_DIKENAL in _kode(hasil)


def test_kecamatan_salah_eja_ditolak():
    hasil = validasi(_berkas(baris(nm_kecamatan="SIDOMUKTY", nm_kelurahan="DUKUH")))

    assert hasil.lolos is False
    assert KECAMATAN_TIDAK_DIKENAL in _kode(hasil)


def test_pasangan_wilayah_salah_ditolak():
    """BUGEL ada di SIDOREJO, bukan TINGKIR."""
    hasil = validasi(_berkas(baris(nm_kecamatan="TINGKIR", nm_kelurahan="BUGEL")))

    assert hasil.lolos is False
    assert PASANGAN_WILAYAH_SALAH in _kode(hasil)


def test_pesan_pasangan_salah_menyebut_kecamatan_yang_benar():
    hasil = validasi(_berkas(baris(nm_kecamatan="TINGKIR", nm_kelurahan="BUGEL")))
    pesan = _cari(hasil, PASANGAN_WILAYAH_SALAH)[0]

    assert "SIDOREJO" in pesan.detail
    assert "TINGKIR" in pesan.detail


def test_sidorejo_kidul_di_tingkir_diterima():
    """Jebakan bagian 5: pasangan ini benar dan tidak boleh ditolak."""
    hasil = validasi(_berkas(baris(nm_kecamatan="TINGKIR", nm_kelurahan="SIDOREJO KIDUL")))

    assert hasil.lolos is True


def test_wilayah_huruf_kecil_dan_spasi_berlebih_diterima():
    hasil = validasi(_berkas(baris(nm_kecamatan=" tingkir ", nm_kelurahan="kutowinangun  lor")))

    assert hasil.lolos is True
    assert hasil.baris[0].kelurahan == "KUTOWINANGUN LOR"


# ---------------------------------------------------------------------------
# A.3 / A.4 — plat dan tanggal
# ---------------------------------------------------------------------------


def test_plat_kosong_ditolak():
    hasil = validasi(_berkas(baris(no_polisi="")))

    assert hasil.lolos is False
    assert PLAT_KOSONG in _kode(hasil)


def test_plat_huruf_kecil_dinormalkan():
    hasil = validasi(_berkas(baris(no_polisi="h1374lk")))

    assert hasil.lolos is True
    assert hasil.baris[0].no_polisi == "H1374LK"


def test_tanggal_kosong_ditolak():
    hasil = validasi(_berkas(baris(tgl_jatuh_tempo_pkb=None)))

    assert hasil.lolos is False
    assert TANGGAL_KOSONG in _kode(hasil)


def test_tanggal_mustahil_ditolak():
    hasil = validasi(_berkas(baris(tgl_jatuh_tempo_pkb="31/02/2026")))

    assert hasil.lolos is False
    assert TANGGAL_TIDAK_VALID in _kode(hasil)


def test_tanggal_format_iso_ditolak():
    hasil = validasi(_berkas(baris(tgl_jatuh_tempo_pkb="2026-05-24")))

    assert hasil.lolos is False
    assert TANGGAL_TIDAK_VALID in _kode(hasil)


def test_tanggal_teks_satu_digit_diterima():
    hasil = validasi(_berkas(baris(tgl_jatuh_tempo_pkb="23/2/2027")))

    assert hasil.lolos is True
    assert hasil.baris[0].tgl_jatuh_tempo_pkb == date(2027, 2, 23)


def test_tanggal_stnk_aneh_tidak_menolak_berkas():
    hasil = validasi(_berkas(baris(tgl_jatuh_tempo_stnk="28/03/0203")))

    assert hasil.lolos is True
    assert hasil.baris[0].tgl_jatuh_tempo_stnk == "28/03/0203"


def test_tanggal_stnk_sel_tanggal_disimpan_dd_mm_yyyy():
    hasil = validasi(_berkas(baris(tgl_jatuh_tempo_stnk=datetime(2030, 3, 28))))

    assert hasil.baris[0].tgl_jatuh_tempo_stnk == "28/03/2030"


# ---------------------------------------------------------------------------
# A.5 / B — jumlah roda
# ---------------------------------------------------------------------------


def test_roda_kosong_ditolak():
    hasil = validasi(_berkas(baris(jml_roda=None)))

    assert hasil.lolos is False
    assert RODA_TIDAK_VALID in _kode(hasil)


def test_roda_nol_ditolak():
    hasil = validasi(_berkas(baris(jml_roda=0)))

    assert hasil.lolos is False
    assert RODA_TIDAK_VALID in _kode(hasil)


def test_roda_berupa_teks_ditolak():
    hasil = validasi(_berkas(baris(jml_roda="abc")))

    assert hasil.lolos is False
    assert RODA_TIDAK_VALID in _kode(hasil)


def test_roda_pecahan_ditolak():
    hasil = validasi(_berkas(baris(jml_roda=2.5)))

    assert hasil.lolos is False
    assert RODA_TIDAK_VALID in _kode(hasil)


def test_roda_tiga_disesuaikan_menjadi_dua():
    hasil = validasi(_berkas(baris(jml_roda=3)))

    assert hasil.lolos is True
    assert hasil.baris[0].jml_roda == 2
    assert RODA_DIUBAH_KE_2 in _kode_peringatan(hasil)


def test_roda_satu_disesuaikan_menjadi_dua():
    hasil = validasi(_berkas(baris(jml_roda=1)))

    assert hasil.baris[0].jml_roda == 2
    assert RODA_DIUBAH_KE_2 in _kode_peringatan(hasil)


def test_roda_enam_dan_delapan_disesuaikan_menjadi_empat():
    hasil = validasi(_berkas(baris(jml_roda=6), baris(no_polisi="H2AA", jml_roda=8)))

    assert hasil.lolos is True
    assert [b.jml_roda for b in hasil.baris] == [4, 4]
    assert RODA_DIUBAH_KE_4 in _kode_peringatan(hasil)


def test_peringatan_roda_mencatat_nomor_baris():
    hasil = validasi(_berkas(baris(), baris(no_polisi="H2AA", jml_roda=6)))
    peringatan = next(p for p in hasil.peringatan if p.kode == RODA_DIUBAH_KE_4)

    assert peringatan.baris == [3]


def test_roda_dua_dan_empat_tidak_memicu_peringatan():
    hasil = validasi(_berkas(baris(jml_roda=2), baris(no_polisi="H2AA", jml_roda=4)))

    assert hasil.peringatan == []


# ---------------------------------------------------------------------------
# A.6 / B — kolom uang
# ---------------------------------------------------------------------------


def test_nilai_inti_kosong_ditolak():
    hasil = validasi(_berkas(baris(**{"PKB Opsen": None})))

    assert hasil.lolos is False
    assert NILAI_INTI_KOSONG in _kode(hasil)


def test_nilai_inti_berisi_strip_dianggap_kosong():
    hasil = validasi(_berkas(baris(**{"PKB Opsen": "-"})))

    assert hasil.lolos is False
    assert NILAI_INTI_KOSONG in _kode(hasil)


def test_nilai_inti_bukan_angka_ditolak():
    hasil = validasi(_berkas(baris(**{"PKB Pokok": "abc"})))

    assert hasil.lolos is False
    assert NILAI_INTI_TIDAK_VALID in _kode(hasil)


def test_nilai_inti_negatif_ditolak():
    hasil = validasi(_berkas(baris(**{"PKB Pokok": -500})))

    assert hasil.lolos is False
    assert NILAI_INTI_TIDAK_VALID in _kode(hasil)


def test_nilai_inti_nol_diterima():
    hasil = validasi(_berkas(baris(**{"SWDKLLJ": 0})))

    assert hasil.lolos is True
    assert hasil.baris[0].swdkllj == Decimal("0")


def test_denda_bukan_angka_ditolak():
    hasil = validasi(_berkas(baris(**{"PKB Denda": "abc"})))

    assert hasil.lolos is False
    assert NILAI_DENDA_TIDAK_VALID in _kode(hasil)


def test_denda_negatif_ditolak():
    hasil = validasi(_berkas(baris(**{"PKB Denda": -100})))

    assert hasil.lolos is False
    assert NILAI_DENDA_TIDAK_VALID in _kode(hasil)


def test_denda_kosong_diisi_nol_dengan_peringatan():
    hasil = validasi(_berkas(baris(**{"PKB Denda": None})))

    assert hasil.lolos is True
    assert hasil.baris[0].pkb_denda == Decimal("0")
    assert DENDA_DIISI_NOL in _kode_peringatan(hasil)


def test_peringatan_denda_menghitung_sel_bukan_baris():
    """Satu baris dengan dua sel kosong berarti dua sel yang disesuaikan."""
    hasil = validasi(_berkas(baris(**{"PKB Denda": None, "PNBP": None})))
    peringatan = next(p for p in hasil.peringatan if p.kode == DENDA_DIISI_NOL)

    assert "2" in peringatan.pesan


def test_total_kosong_dihitung_ulang_dari_kolom_14_sampai_20():
    hasil = validasi(_berkas(baris(TOTAL=None)))

    # 6500 + 500 + 4500 + 500 + 35000 + 8000 + 0
    assert hasil.baris[0].total == Decimal("55000")


def test_total_terisi_dipakai_apa_adanya():
    hasil = validasi(_berkas(baris(TOTAL=99999)))

    assert hasil.baris[0].total == Decimal("99999")


# ---------------------------------------------------------------------------
# A.7 — baris kembar
# ---------------------------------------------------------------------------


def test_plat_dan_tanggal_sama_ditolak():
    hasil = validasi(
        _berkas(
            baris(no_polisi="H1234AB", tgl_jatuh_tempo_pkb=datetime(2026, 5, 24)),
            baris(no_polisi="H1234AB", tgl_jatuh_tempo_pkb=datetime(2026, 5, 24)),
        )
    )

    assert hasil.lolos is False
    assert BARIS_KEMBAR in _kode(hasil)


def test_kembar_dideteksi_setelah_plat_dinormalkan():
    hasil = validasi(
        _berkas(
            baris(no_polisi="H 1234 AB", tgl_jatuh_tempo_pkb=datetime(2026, 5, 24)),
            baris(no_polisi="h1234ab", tgl_jatuh_tempo_pkb=datetime(2026, 5, 24)),
        )
    )

    assert BARIS_KEMBAR in _kode(hasil)


def test_pesan_kembar_menyebut_kedua_nomor_baris():
    hasil = validasi(
        _berkas(
            baris(no_polisi="H1234AB", tgl_jatuh_tempo_pkb=datetime(2026, 5, 24)),
            baris(no_polisi="H1234AB", tgl_jatuh_tempo_pkb=datetime(2026, 5, 24)),
        )
    )

    assert _cari(hasil, BARIS_KEMBAR)[0].baris == [2, 3]


def test_plat_sama_tanggal_berbeda_diterima():
    hasil = validasi(
        _berkas(
            baris(no_polisi="H1234AB", tgl_jatuh_tempo_pkb=datetime(2025, 5, 24)),
            baris(no_polisi="H1234AB", tgl_jatuh_tempo_pkb=datetime(2026, 5, 24)),
        )
    )

    assert hasil.lolos is True


# ---------------------------------------------------------------------------
# Pengumpulan dan pengelompokan kesalahan
# ---------------------------------------------------------------------------


def test_seluruh_kesalahan_dilaporkan_sekaligus():
    hasil = validasi(
        _berkas(
            baris(no_polisi=""),
            baris(no_polisi="H2AA", jml_roda="abc"),
            baris(no_polisi="H3AA", nm_kelurahan="TIDAK ADA"),
            baris(no_polisi="H4AA", **{"PKB Opsen": None}),
        )
    )

    assert hasil.lolos is False
    assert _kode(hasil) == {
        PLAT_KOSONG,
        RODA_TIDAK_VALID,
        KELURAHAN_TIDAK_DIKENAL,
        NILAI_INTI_KOSONG,
    }


def test_kesalahan_sejenis_dikelompokkan_menjadi_satu_entri():
    hasil = validasi(
        _berkas(
            baris(no_polisi="H1AA", nm_kelurahan="TINGKR LOR"),
            baris(no_polisi="H2AA", nm_kelurahan="TINGKR LOR"),
            baris(no_polisi="H3AA", nm_kelurahan="TINGKR LOR"),
        )
    )
    entri = _cari(hasil, KELURAHAN_TIDAK_DIKENAL)

    assert len(entri) == 1
    assert entri[0].baris == [2, 3, 4]


def test_nilai_berbeda_menjadi_entri_terpisah():
    hasil = validasi(
        _berkas(
            baris(no_polisi="H1AA", nm_kelurahan="TINGKR LOR"),
            baris(no_polisi="H2AA", nm_kelurahan="BLOTONGN"),
        )
    )

    assert len(_cari(hasil, KELURAHAN_TIDAK_DIKENAL)) == 2


def test_baris_cacat_tidak_ikut_ke_daftar_siap_simpan():
    hasil = validasi(_berkas(baris(no_polisi="")))

    assert hasil.baris == []


# ---------------------------------------------------------------------------
# Ringkasan
# ---------------------------------------------------------------------------


def test_ringkasan_mencatat_jumlah_baris_terbaca():
    hasil = validasi(_berkas(baris(no_polisi="H1AA"), baris(no_polisi="H2AA")))

    assert hasil.ringkasan.baris_terbaca == 2


def test_ringkasan_mencatat_rentang_tanggal():
    hasil = validasi(
        _berkas(
            baris(no_polisi="H1AA", tgl_jatuh_tempo_pkb=datetime(2021, 1, 2)),
            baris(no_polisi="H2AA", tgl_jatuh_tempo_pkb=datetime(2028, 2, 27)),
        )
    )

    assert hasil.ringkasan.tanggal_awal == date(2021, 1, 2)
    assert hasil.ringkasan.tanggal_akhir == date(2028, 2, 27)


def test_ringkasan_menghitung_wilayah_yang_terwakili():
    hasil = validasi(
        _berkas(
            baris(no_polisi="H1AA", nm_kecamatan="TINGKIR", nm_kelurahan="TINGKIR LOR"),
            baris(no_polisi="H2AA", nm_kecamatan="SIDOREJO", nm_kelurahan="BUGEL"),
        )
    )

    assert hasil.ringkasan.kecamatan_ada == 2
    assert hasil.ringkasan.kecamatan_master == 4
    assert hasil.ringkasan.kelurahan_ada == 2
    assert hasil.ringkasan.kelurahan_master == 23
