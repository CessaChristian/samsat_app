"""Tes integrasi: unggah berkas contoh lewat API, lalu periksa /api/rekap.

Ini kriteria selesai Tahap 5 pada bagian 16, diuji terhadap angka acuan
bagian 17.1 dengan ``APP_TODAY=2026-09-19``.
"""

import io

import pytest

from app.config import AKAR_PROYEK

BERKAS_CONTOH = AKAR_PROYEK / "samples" / "data_dummy_bersih.xlsx"

pytestmark = pytest.mark.skipif(
    not BERKAS_CONTOH.is_file(),
    reason=f"berkas contoh tidak tersedia di {BERKAS_CONTOH}",
)

HARI_ACUAN = "2026-09-19"


@pytest.fixture(autouse=True)
def tanggal_tetap(monkeypatch):
    monkeypatch.setenv("APP_TODAY", HARI_ACUAN)


@pytest.fixture
def dashboard_terisi(klien_masuk):
    """Berkas contoh diunggah lewat alur Cek File -> Simpan yang sebenarnya."""
    isi = BERKAS_CONTOH.read_bytes()
    cek = klien_masuk.post(
        "/api/upload/check",
        data={"file": (io.BytesIO(isi), BERKAS_CONTOH.name)},
        content_type="multipart/form-data",
    ).get_json()
    assert cek["lolos"] is True, cek["kesalahan"][:3]

    simpan = klien_masuk.post("/api/upload/commit", json={"token": cek["token"]})
    assert simpan.status_code == 200
    return klien_masuk


def test_alur_unggah_melaporkan_seluruh_baris(klien_masuk):
    isi = BERKAS_CONTOH.read_bytes()
    cek = klien_masuk.post(
        "/api/upload/check",
        data={"file": (io.BytesIO(isi), BERKAS_CONTOH.name)},
        content_type="multipart/form-data",
    ).get_json()

    assert cek["ringkasan"]["baris_terbaca"] == 4822
    assert cek["ringkasan"]["baris_baru"] == 4822
    assert cek["ringkasan"]["kelurahan_ada"] == 19
    assert cek["ringkasan"]["kecamatan_ada"] == 3

    hasil = klien_masuk.post("/api/upload/commit", json={"token": cek["token"]}).get_json()
    assert hasil["jumlah_baris"] == 4822


def test_meta_setelah_unggah(dashboard_terisi):
    isi = dashboard_terisi.get("/api/meta").get_json()

    assert isi["ada_data"] is True
    assert isi["periode"]["awal"] == "2021-01-02"
    # MAX di data adalah 27/02/2028, dipotong menjadi hari ini.
    assert isi["periode"]["akhir"] == HARI_ACUAN
    assert isi["batch_terakhir"]["jumlah_baris"] == 4822


def test_kartu_sesuai_angka_acuan(dashboard_terisi):
    kpi = dashboard_terisi.get("/api/rekap").get_json()["kpi"]

    assert kpi["objek"] == 4645
    assert kpi["pkb"] == 8_859_350_800
    assert kpi["opsen_pkb"] == 3_430_740_400
    assert kpi["swdkllj"] == 1_494_891_000


def test_komposisi_sesuai_angka_acuan(dashboard_terisi):
    komposisi = dashboard_terisi.get("/api/rekap").get_json()["komposisi"]

    assert {k["roda"]: k["objek"] for k in komposisi} == {2: 528, 4: 4117}


def test_angka_tengah_donut_seratus_persen_tanpa_filter(dashboard_terisi):
    persentase = dashboard_terisi.get("/api/rekap").get_json()["persentase"]

    assert persentase["objek_filter"] == 4645
    assert persentase["objek_periode"] == 4645
    assert persentase["persen"] == 100.0


def test_pkb_per_kecamatan_sesuai_angka_acuan(dashboard_terisi):
    per_kecamatan = dashboard_terisi.get("/api/rekap").get_json()["per_kecamatan"]

    assert [(k["kecamatan"], k["pkb"]) for k in per_kecamatan] == [
        ("SIDOREJO", 6_211_792_200),
        ("ARGOMULYO", 1_600_389_500),
        ("TINGKIR", 1_047_169_100),
        ("SIDOMUKTI", 0),
    ]


def test_tabel_rincian_menampilkan_23_kelurahan(dashboard_terisi):
    per_wilayah = dashboard_terisi.get("/api/rekap").get_json()["per_wilayah"]

    assert len(per_wilayah) == 23
    berisi = [w for w in per_wilayah if w["objek"] > 0]
    assert len(berisi) == 19

    sidomukti = [w for w in per_wilayah if w["kecamatan"] == "SIDOMUKTI"]
    assert len(sidomukti) == 4
    assert all(w["objek"] == 0 and w["pkb"] == 0 for w in sidomukti)


def test_baris_total_cocok_dengan_kartu(dashboard_terisi):
    isi = dashboard_terisi.get("/api/rekap").get_json()

    assert isi["total"]["objek"] == isi["kpi"]["objek"]
    assert isi["total"]["pkb"] == isi["kpi"]["pkb"]
    assert isi["total"]["pkb"] == sum(w["pkb"] for w in isi["per_wilayah"])


def test_persen_kelurahan_berjumlah_seratus(dashboard_terisi):
    per_wilayah = dashboard_terisi.get("/api/rekap").get_json()["per_wilayah"]

    assert sum(w["persen"] for w in per_wilayah) == pytest.approx(100.0, abs=0.5)


def test_filter_status_membagi_habis_objek_periode(dashboard_terisi):
    """Angka acuan 17.1 menyebut 6 baris lunas untuk **seluruh tabel**.

    Rekap hanya menghitung baris di dalam periode, dan satu di antara keenam
    baris lunas itu (H1079AB, jatuh tempo 20/02/2027) berada di luar periode
    karena platnya punya baris 28/06/2027 yang lebih baru. Jadi yang tampil 5.
    """
    lunas = dashboard_terisi.get("/api/rekap?status=LUNAS").get_json()["kpi"]["objek"]
    belum = dashboard_terisi.get("/api/rekap?status=BELUM_LUNAS").get_json()["kpi"]["objek"]

    assert lunas == 5
    assert belum == 4640
    assert lunas + belum == 4645


def test_filter_kecamatan_membatasi_tabel_tapi_grafik_tetap_empat(dashboard_terisi):
    isi = dashboard_terisi.get("/api/rekap?kecamatan=SIDOREJO").get_json()

    assert isi["kpi"]["pkb"] == 6_211_792_200
    assert len(isi["per_wilayah"]) == 6
    assert len(isi["per_kecamatan"]) == 4


def test_opsen_tidak_sama_dengan_66_persen_pkb(dashboard_terisi):
    """Prototipe menghitung Opsen 66% dari PKB; data sebenarnya tidak begitu."""
    kpi = dashboard_terisi.get("/api/rekap").get_json()["kpi"]

    assert kpi["opsen_pkb"] != round(kpi["pkb"] * 0.66)
