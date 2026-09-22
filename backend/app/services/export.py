"""Bagian bersama export Excel dan PDF (bagian 13).

Isi kedua export sama: seluruh baris detail yang lolos filter aktif, dengan
21 kolom persis seperti bagian 4. Yang berbeda hanya cara menuliskannya.
"""

from datetime import date

from app.services.normalisasi import NilaiTidakValid, ke_tanggal

#: Nama header berkas pusat -> nama kolom pada hasil ``export_detail.sql``.
#: Urutan penulisan diambil dari ``HEADER_WAJIB``, bukan dari kamus ini.
PETA_KOLOM: dict[str, str] = {
    "no_polisi": "no_polisi",
    "nama": "nama",
    "alamat": "alamat",
    "nm_kecamatan": "nm_kecamatan",
    "nm_kelurahan": "nm_kelurahan",
    "nm_jenis_kend": "nm_jenis_kend",
    "nm_merk_kend": "nm_merk_kend",
    "th_buat": "th_buat",
    "warna_kend": "warna_kend",
    "warna_tnkb_kend": "warna_tnkb_kend",
    "jml_roda": "jml_roda",
    "tgl_jatuh_tempo_pkb": "tgl_jatuh_tempo_pkb",
    "tgl_jatuh_tempo_stnk": "tgl_jatuh_tempo_stnk",
    "PKB Pokok": "pkb_pokok",
    "PKB Denda": "pkb_denda",
    "PKB Opsen": "pkb_opsen",
    "PKB Denda Opsen": "pkb_denda_opsen",
    "SWDKLLJ": "swdkllj",
    "Denda SWDKLLJ": "denda_swdkllj",
    "PNBP": "pnbp",
    "TOTAL": "total",
}

#: Ditulis sebagai angka, bukan teks.
KOLOM_UANG: frozenset[str] = frozenset(
    {
        "PKB Pokok",
        "PKB Denda",
        "PKB Opsen",
        "PKB Denda Opsen",
        "SWDKLLJ",
        "Denda SWDKLLJ",
        "PNBP",
        "TOTAL",
    }
)


def tanggal_stnk(nilai) -> date | None:
    """Jatuh tempo STNK disimpan sebagai teks dan boleh berisi apa saja.

    Bila bentuknya ``dd/mm/yyyy`` yang sah, kembalikan tanggalnya supaya bisa
    ditulis sebagai sel tanggal. Isi lain — misalnya "SEUMUR HIDUP" —
    mengembalikan ``None`` dan ditulis apa adanya (bagian 13).
    """
    try:
        return ke_tanggal(nilai)
    except NilaiTidakValid:
        return None
