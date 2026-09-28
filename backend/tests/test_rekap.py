"""Tes untuk perhitungan dashboard dan endpoint /api/meta serta /api/rekap.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 7.2 (batas periode), 11 (API),
dan 12 (perhitungan).
"""

from datetime import date
from decimal import Decimal

import pytest

from app.services.penyimpan import simpan
from tests.bantu import bersih

HARI_ACUAN = "2026-09-19"


@pytest.fixture(autouse=True)
def tanggal_tetap(monkeypatch):
    """Kunci "hari ini" supaya batas periode dapat diuji."""
    monkeypatch.setenv("APP_TODAY", HARI_ACUAN)


def _isi(baris, nama="rekap.xlsx", hash_file="d" * 64):
    return simpan(baris, nama_file=nama, hash_file=hash_file, ukuran_byte=1)


# ---------------------------------------------------------------------------
# /api/meta
# ---------------------------------------------------------------------------


def test_meta_tanpa_sesi_ditolak(klien):
    assert klien.get("/api/meta").status_code == 401


def test_meta_saat_database_kosong(klien_masuk):
    isi = klien_masuk.get("/api/meta").get_json()

    assert isi["ada_data"] is False
    assert isi["periode"]["awal"] is None
    assert isi["batch_terakhir"] is None


def test_meta_selalu_memuat_master_wilayah(klien_masuk):
    isi = klien_masuk.get("/api/meta").get_json()

    assert len(isi["wilayah"]) == 4
    assert sum(len(w["kelurahan"]) for w in isi["wilayah"]) == 23


def test_meta_memuat_pilihan_filter(klien_masuk):
    isi = klien_masuk.get("/api/meta").get_json()

    assert isi["opsi"]["roda"] == [2, 4]
    assert isi["opsi"]["status"] == ["LUNAS", "BELUM_LUNAS"]


def test_meta_melaporkan_rentang_periode(klien_masuk):
    _isi(
        [
            bersih(no_polisi="H1AA", tgl_jatuh_tempo_pkb=date(2021, 1, 2)),
            bersih(no_polisi="H2AA", tgl_jatuh_tempo_pkb=date(2026, 3, 10)),
        ]
    )

    isi = klien_masuk.get("/api/meta").get_json()

    assert isi["ada_data"] is True
    assert isi["periode"]["awal"] == "2021-01-02"
    assert isi["periode"]["akhir"] == "2026-03-10"


def test_periode_tidak_pernah_melewati_hari_ini(klien_masuk):
    """Jatuh tempo masa depan hanya penanda lunas, bukan periode."""
    _isi(
        [
            bersih(no_polisi="H1AA", tgl_jatuh_tempo_pkb=date(2026, 1, 5)),
            bersih(no_polisi="H2AA", tgl_jatuh_tempo_pkb=date(2028, 2, 27)),
        ]
    )

    isi = klien_masuk.get("/api/meta").get_json()

    assert isi["periode"]["akhir"] == HARI_ACUAN


def test_meta_menyebut_batch_terakhir(klien_masuk):
    _isi([bersih()], nama="rekap-2026-09-18.xlsx")

    isi = klien_masuk.get("/api/meta").get_json()

    assert isi["batch_terakhir"]["nama_file"] == "rekap-2026-09-18.xlsx"
    assert isi["batch_terakhir"]["jumlah_baris"] == 1
    assert isi["batch_terakhir"]["disimpan_pada"]


# ---------------------------------------------------------------------------
# /api/rekap — bentuk dan perhitungan dasar
# ---------------------------------------------------------------------------


def test_rekap_tanpa_sesi_ditolak(klien):
    assert klien.get("/api/rekap").status_code == 401


def test_rekap_saat_kosong_menampilkan_kerangka_lengkap(klien_masuk):
    isi = klien_masuk.get("/api/rekap").get_json()

    assert isi["kpi"] == {"objek": 0, "pkb": 0, "opsen_pkb": 0, "swdkllj": 0}
    assert len(isi["per_wilayah"]) == 23
    assert len(isi["per_kecamatan"]) == 4


def test_kartu_menjumlahkan_pokok_dan_denda(klien_masuk):
    _isi([bersih()])

    kpi = klien_masuk.get("/api/rekap").get_json()["kpi"]

    assert kpi["objek"] == 1
    assert kpi["pkb"] == 7000        # 6500 + 500
    assert kpi["opsen_pkb"] == 5000  # 4500 + 500
    assert kpi["swdkllj"] == 43000   # 35000 + 8000


def test_uang_dikirim_sebagai_angka_bulat(klien_masuk):
    _isi([bersih()])

    kpi = klien_masuk.get("/api/rekap").get_json()["kpi"]

    assert isinstance(kpi["pkb"], int)


def test_baris_masa_depan_tidak_ikut_dihitung(klien_masuk):
    _isi(
        [
            bersih(no_polisi="H1AA", tgl_jatuh_tempo_pkb=date(2026, 1, 5)),
            bersih(no_polisi="H2AA", tgl_jatuh_tempo_pkb=date(2027, 1, 5)),
        ]
    )

    assert klien_masuk.get("/api/rekap").get_json()["kpi"]["objek"] == 1


def test_tabel_selalu_memuat_23_kelurahan(klien_masuk):
    _isi([bersih()])

    per_wilayah = klien_masuk.get("/api/rekap").get_json()["per_wilayah"]

    assert len(per_wilayah) == 23
    kosong = [w for w in per_wilayah if w["kelurahan"] == "CEBONGAN"][0]
    assert kosong["objek"] == 0
    assert kosong["pkb"] == 0


def test_tabel_diurutkan_pkb_menurun(klien_masuk):
    _isi(
        [
            bersih(no_polisi="H1AA", kelurahan="BUGEL", kecamatan="SIDOREJO",
                   pkb_pokok=Decimal("100")),
            bersih(no_polisi="H2AA", kelurahan="TINGKIR LOR", kecamatan="TINGKIR",
                   pkb_pokok=Decimal("900")),
        ]
    )

    per_wilayah = klien_masuk.get("/api/rekap").get_json()["per_wilayah"]

    assert per_wilayah[0]["kelurahan"] == "TINGKIR LOR"
    assert per_wilayah[1]["kelurahan"] == "BUGEL"


def test_empat_kecamatan_selalu_tampil_walau_kosong(klien_masuk):
    _isi([bersih()])

    per_kecamatan = klien_masuk.get("/api/rekap").get_json()["per_kecamatan"]

    assert {k["kecamatan"] for k in per_kecamatan} == {
        "ARGOMULYO",
        "SIDOMUKTI",
        "SIDOREJO",
        "TINGKIR",
    }


def test_baris_total_menjumlahkan_seluruh_tabel(klien_masuk):
    _isi([bersih(no_polisi="H1AA"), bersih(no_polisi="H2AA")])

    isi = klien_masuk.get("/api/rekap").get_json()

    assert isi["total"]["objek"] == 2
    assert isi["total"]["pkb"] == sum(w["pkb"] for w in isi["per_wilayah"])


def test_komposisi_roda(klien_masuk):
    _isi(
        [
            bersih(no_polisi="H1AA", jml_roda=2),
            bersih(no_polisi="H2AA", jml_roda=4),
            bersih(no_polisi="H3AA", jml_roda=4),
        ]
    )

    komposisi = klien_masuk.get("/api/rekap").get_json()["komposisi"]

    assert {k["roda"]: k["objek"] for k in komposisi} == {2: 1, 4: 2}


def test_komposisi_selalu_memuat_roda_2_dan_4(klien_masuk):
    _isi([bersih(jml_roda=4)])

    komposisi = klien_masuk.get("/api/rekap").get_json()["komposisi"]

    assert {k["roda"] for k in komposisi} == {2, 4}


# ---------------------------------------------------------------------------
# Angka tengah donut (bagian 12)
# ---------------------------------------------------------------------------


def test_persentase_100_bila_tanpa_filter(klien_masuk):
    _isi([bersih(no_polisi="H1AA"), bersih(no_polisi="H2AA")])

    persentase = klien_masuk.get("/api/rekap").get_json()["persentase"]

    assert persentase["objek_filter"] == 2
    assert persentase["objek_periode"] == 2
    assert persentase["persen"] == 100.0


def test_persentase_membandingkan_dengan_periode_tanpa_filter_lain(klien_masuk):
    _isi(
        [
            bersih(no_polisi="H1AA", jml_roda=2),
            bersih(no_polisi="H2AA", jml_roda=4),
            bersih(no_polisi="H3AA", jml_roda=4),
            bersih(no_polisi="H4AA", jml_roda=4),
        ]
    )

    persentase = klien_masuk.get("/api/rekap?roda=2").get_json()["persentase"]

    assert persentase["objek_filter"] == 1
    assert persentase["objek_periode"] == 4
    assert persentase["persen"] == 25.0


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------


def test_filter_roda(klien_masuk):
    _isi([bersih(no_polisi="H1AA", jml_roda=2), bersih(no_polisi="H2AA", jml_roda=4)])

    assert klien_masuk.get("/api/rekap?roda=4").get_json()["kpi"]["objek"] == 1


def test_filter_status_belum_lunas(klien_masuk):
    _isi(
        [
            bersih(no_polisi="H1AA", tgl_jatuh_tempo_pkb=date(2025, 5, 24)),
            bersih(no_polisi="H1AA", tgl_jatuh_tempo_pkb=date(2026, 5, 24)),
        ]
    )

    lunas = klien_masuk.get("/api/rekap?status=LUNAS").get_json()["kpi"]["objek"]
    belum = klien_masuk.get("/api/rekap?status=BELUM_LUNAS").get_json()["kpi"]["objek"]

    assert lunas == 1
    assert belum == 1


def test_filter_kecamatan(klien_masuk):
    _isi(
        [
            bersih(no_polisi="H1AA", kecamatan="TINGKIR", kelurahan="TINGKIR LOR"),
            bersih(no_polisi="H2AA", kecamatan="SIDOREJO", kelurahan="BUGEL"),
        ]
    )

    isi = klien_masuk.get("/api/rekap?kecamatan=TINGKIR").get_json()

    assert isi["kpi"]["objek"] == 1
    assert {w["kecamatan"] for w in isi["per_wilayah"]} == {"TINGKIR"}
    assert len(isi["per_wilayah"]) == 7


def test_filter_kelurahan(klien_masuk):
    _isi(
        [
            bersih(no_polisi="H1AA", kecamatan="TINGKIR", kelurahan="TINGKIR LOR"),
            bersih(no_polisi="H2AA", kecamatan="TINGKIR", kelurahan="GENDONGAN"),
        ]
    )

    isi = klien_masuk.get("/api/rekap?kelurahan=TINGKIR LOR").get_json()

    assert isi["kpi"]["objek"] == 1
    assert len(isi["per_wilayah"]) == 1


def test_filter_tanggal(klien_masuk):
    _isi(
        [
            bersih(no_polisi="H1AA", tgl_jatuh_tempo_pkb=date(2026, 1, 15)),
            bersih(no_polisi="H2AA", tgl_jatuh_tempo_pkb=date(2026, 6, 15)),
        ]
    )

    isi = klien_masuk.get("/api/rekap?dari=2026-01-01&sampai=2026-03-31").get_json()

    assert isi["kpi"]["objek"] == 1


def test_sampai_yang_melewati_hari_ini_dipotong(klien_masuk):
    _isi([bersih(tgl_jatuh_tempo_pkb=date(2026, 1, 5))])

    isi = klien_masuk.get("/api/rekap?dari=2026-01-01&sampai=2030-12-31").get_json()

    assert isi["periode"]["sampai"] == HARI_ACUAN


def test_filter_gabungan(klien_masuk):
    _isi(
        [
            bersih(no_polisi="H1AA", kecamatan="TINGKIR", kelurahan="TINGKIR LOR", jml_roda=2),
            bersih(no_polisi="H2AA", kecamatan="TINGKIR", kelurahan="TINGKIR LOR", jml_roda=4),
            bersih(no_polisi="H3AA", kecamatan="SIDOREJO", kelurahan="BUGEL", jml_roda=2),
        ]
    )

    isi = klien_masuk.get("/api/rekap?kecamatan=TINGKIR&roda=2").get_json()

    assert isi["kpi"]["objek"] == 1


@pytest.mark.parametrize(
    "kueri",
    ["roda=3", "roda=abc", "status=MUNGKIN", "dari=bukan-tanggal", "kecamatan=TIDAK ADA"],
)
def test_filter_tidak_masuk_akal_ditolak(klien_masuk, kueri):
    balasan = klien_masuk.get(f"/api/rekap?{kueri}")

    assert balasan.status_code == 400
    # Kode pesannya ikut diperiksa: frontend membedakan jenis kesalahan lewat
    # medan ini, jadi salah ketik satu huruf pun harus tertangkap.
    assert balasan.get_json()["kode"] == "FILTER_TIDAK_VALID"
