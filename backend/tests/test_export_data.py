"""Tes sumber baris export (bagian 13).

Isi export Excel dan PDF sama: seluruh baris detail yang lolos filter aktif,
21 kolom seperti bagian 4, diurutkan kecamatan, kelurahan, no_polisi,
tgl_jatuh_tempo_pkb.
"""

from datetime import date

from app.models.kewajiban import detail
from app.services.rekap import Filter
from app.services.penyimpan import simpan
from tests.bantu import bersih


def _simpan(baris):
    return simpan(
        baris, nama_file="rekap.xlsx", hash_file="a" * 64, ukuran_byte=1024, peringatan=[]
    )


def _saringan(**ubahan):
    dasar = {"dari": date(2020, 1, 1), "sampai": date(2027, 12, 31)}
    dasar.update(ubahan)
    return Filter(**dasar)


def test_baris_diurutkan_kecamatan_kelurahan_plat_lalu_jatuh_tempo(db):
    _simpan(
        [
            bersih(no_polisi="H9999ZZ", kecamatan="SIDOREJO", kelurahan="SALATIGA"),
            bersih(no_polisi="H1111AA", kecamatan="TINGKIR", kelurahan="TINGKIR LOR"),
            bersih(no_polisi="H1111AA", kecamatan="TINGKIR", kelurahan="TINGKIR LOR",
                   tgl_jatuh_tempo_pkb=date(2025, 1, 10)),
            bersih(no_polisi="H2222BB", kecamatan="SIDOREJO", kelurahan="BLOTONGAN"),
        ]
    )

    urutan = [
        (b["nm_kecamatan"], b["nm_kelurahan"], b["no_polisi"], b["tgl_jatuh_tempo_pkb"])
        for b in detail(_saringan())
    ]

    assert urutan == [
        ("SIDOREJO", "BLOTONGAN", "H2222BB", date(2026, 5, 24)),
        ("SIDOREJO", "SALATIGA", "H9999ZZ", date(2026, 5, 24)),
        ("TINGKIR", "TINGKIR LOR", "H1111AA", date(2025, 1, 10)),
        ("TINGKIR", "TINGKIR LOR", "H1111AA", date(2026, 5, 24)),
    ]


def test_filter_kecamatan_membatasi_baris(db):
    _simpan(
        [
            bersih(no_polisi="H1111AA", kecamatan="SIDOREJO", kelurahan="SALATIGA"),
            bersih(no_polisi="H2222BB", kecamatan="TINGKIR", kelurahan="TINGKIR LOR"),
        ]
    )

    plat = [b["no_polisi"] for b in detail(_saringan(kecamatan="TINGKIR"))]

    assert plat == ["H2222BB"]


def test_periode_membatasi_baris(db):
    _simpan(
        [
            bersih(no_polisi="H1111AA", tgl_jatuh_tempo_pkb=date(2024, 3, 5)),
            bersih(no_polisi="H2222BB", tgl_jatuh_tempo_pkb=date(2026, 5, 24)),
        ]
    )

    plat = [
        b["no_polisi"]
        for b in detail(_saringan(dari=date(2026, 1, 1), sampai=date(2026, 12, 31)))
    ]

    assert plat == ["H2222BB"]


def test_baris_memuat_kolom_yang_hanya_dipakai_export(db):
    """nama dan alamat tidak dipakai dashboard, tetapi wajib ada di export."""
    _simpan([bersih()])

    baris = next(iter(detail(_saringan())))

    assert baris["nama"] == "RUSIYATI"
    assert baris["alamat"] == "JL TIRTOYOSO I/09 RT07/IX SLTG"
    assert baris["nm_merk_kend"] == "TOYOTA"
    assert baris["tgl_jatuh_tempo_stnk"] == "24/05/2030"
