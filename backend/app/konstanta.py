"""Konstanta domain: header berkas pusat, master wilayah, dan kode pesan.

Semuanya dikumpulkan di satu berkas karena spesifikasi bagian 4 mencatat
bahwa **format header berkas pusat belum final** (menunggu keputusan atasan).
Bila header berubah, hanya berkas ini yang perlu disunting.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 4, 5, 9, dan 18.
"""

# ---------------------------------------------------------------------------
# Header berkas Excel dari pusat (bagian 4)
# ---------------------------------------------------------------------------

#: Ke-21 nama header, urut seperti berkas acuan. Urutan kolom di berkas yang
#: diunggah boleh berbeda; urutan di sini dipakai untuk export (bagian 13).
HEADER_WAJIB: tuple[str, ...] = (
    "no_polisi",
    "nama",
    "alamat",
    "nm_kecamatan",
    "nm_kelurahan",
    "nm_jenis_kend",
    "nm_merk_kend",
    "th_buat",
    "warna_kend",
    "warna_tnkb_kend",
    "jml_roda",
    "tgl_jatuh_tempo_pkb",
    "tgl_jatuh_tempo_stnk",
    "PKB Pokok",
    "PKB Denda",
    "PKB Opsen",
    "PKB Denda Opsen",
    "SWDKLLJ",
    "Denda SWDKLLJ",
    "PNBP",
    "TOTAL",
)

#: Wajib terisi. Nilai 0 diperbolehkan, kosong ditolak (bagian 9.A.6a).
KOLOM_NILAI_INTI: tuple[str, ...] = ("PKB Pokok", "PKB Opsen", "SWDKLLJ")

#: Boleh kosong; saat menyimpan diisi 0 dengan peringatan (bagian 9.B).
KOLOM_DENDA_BOLEH_KOSONG: tuple[str, ...] = (
    "PKB Denda",
    "PKB Denda Opsen",
    "Denda SWDKLLJ",
    "PNBP",
)

#: Kolom yang dijumlahkan untuk menghitung ulang TOTAL bila sel TOTAL kosong
#: atau tidak terbaca (bagian 4, kolom 14–20).
KOLOM_PENJUMLAH_TOTAL: tuple[str, ...] = (
    "PKB Pokok",
    "PKB Denda",
    "PKB Opsen",
    "PKB Denda Opsen",
    "SWDKLLJ",
    "Denda SWDKLLJ",
    "PNBP",
)

#: Teks yang dianggap kosong pada pemeriksaan isi sel (bagian 9.A).
TEKS_KOSONG: frozenset[str] = frozenset({"", "-", "--"})


# ---------------------------------------------------------------------------
# Master wilayah Kota Salatiga (bagian 5)
# ---------------------------------------------------------------------------

KECAMATAN: tuple[str, ...] = ("ARGOMULYO", "SIDOMUKTI", "SIDOREJO", "TINGKIR")

#: Sumber kebenaran pasangan kelurahan–kecamatan.
#:
#: Dua jebakan yang dicatat spesifikasi:
#:   * SIDOREJO KIDUL berada di Kecamatan TINGKIR, bukan SIDOREJO.
#:   * SALATIGA adalah nama kelurahan di Kecamatan SIDOREJO.
KELURAHAN_KE_KECAMATAN: dict[str, str] = {
    # ARGOMULYO (6)
    "CEBONGAN": "ARGOMULYO",
    "KUMPULREJO": "ARGOMULYO",
    "LEDOK": "ARGOMULYO",
    "NOBOREJO": "ARGOMULYO",
    "RANDUACIR": "ARGOMULYO",
    "TEGALREJO": "ARGOMULYO",
    # SIDOMUKTI (4)
    "DUKUH": "SIDOMUKTI",
    "KALICACING": "SIDOMUKTI",
    "KECANDRAN": "SIDOMUKTI",
    "MANGUNSARI": "SIDOMUKTI",
    # SIDOREJO (6)
    "BLOTONGAN": "SIDOREJO",
    "BUGEL": "SIDOREJO",
    "KAUMAN KIDUL": "SIDOREJO",
    "PULUTAN": "SIDOREJO",
    "SALATIGA": "SIDOREJO",
    "SIDOREJO LOR": "SIDOREJO",
    # TINGKIR (7)
    "GENDONGAN": "TINGKIR",
    "KALIBENING": "TINGKIR",
    "KUTOWINANGUN KIDUL": "TINGKIR",
    "KUTOWINANGUN LOR": "TINGKIR",
    "SIDOREJO KIDUL": "TINGKIR",
    "TINGKIR LOR": "TINGKIR",
    "TINGKIR TENGAH": "TINGKIR",
}


# ---------------------------------------------------------------------------
# Kode kesalahan yang menolak berkas (bagian 9.A)
# ---------------------------------------------------------------------------

HEADER_KOLOM_HILANG = "HEADER_KOLOM_HILANG"
KELURAHAN_TIDAK_DIKENAL = "KELURAHAN_TIDAK_DIKENAL"
KECAMATAN_TIDAK_DIKENAL = "KECAMATAN_TIDAK_DIKENAL"
PASANGAN_WILAYAH_SALAH = "PASANGAN_WILAYAH_SALAH"
PLAT_KOSONG = "PLAT_KOSONG"
TANGGAL_KOSONG = "TANGGAL_KOSONG"
TANGGAL_TIDAK_VALID = "TANGGAL_TIDAK_VALID"
RODA_TIDAK_VALID = "RODA_TIDAK_VALID"
NILAI_INTI_KOSONG = "NILAI_INTI_KOSONG"
NILAI_INTI_TIDAK_VALID = "NILAI_INTI_TIDAK_VALID"
NILAI_DENDA_TIDAK_VALID = "NILAI_DENDA_TIDAK_VALID"
BARIS_KEMBAR = "BARIS_KEMBAR"

# Kesalahan tingkat berkas, bukan isi (bagian 11).
BERKAS_TIDAK_TERBACA = "BERKAS_TIDAK_TERBACA"
FORMAT_TIDAK_DIDUKUNG = "FORMAT_TIDAK_DIDUKUNG"
BERKAS_TERLALU_BESAR = "BERKAS_TERLALU_BESAR"


# ---------------------------------------------------------------------------
# Kode penyesuaian otomatis, berkas tetap diterima (bagian 9.B)
# ---------------------------------------------------------------------------

RODA_DIUBAH_KE_2 = "RODA_DIUBAH_KE_2"
RODA_DIUBAH_KE_4 = "RODA_DIUBAH_KE_4"
DENDA_DIISI_NOL = "DENDA_DIISI_NOL"
BERKAS_PERNAH_DISIMPAN = "BERKAS_PERNAH_DISIMPAN"


# ---------------------------------------------------------------------------
# Ambang saran ejaan untuk nama wilayah yang tidak dikenal (bagian 9.A)
# ---------------------------------------------------------------------------

JARAK_SARAN_MAKS = 3
