"""Validasi isi berkas Excel dari pusat.

Fungsi di berkas ini **murni**: tidak menyentuh database, tidak membaca disk,
tidak memanggil jam. Masukannya :class:`~app.services.pembaca.BerkasExcel`,
keluarannya :class:`HasilValidasi`.

Urutan pemrosesan:

1. Tahap header (A.1). Gagal -> berhenti; kolom lain memang tidak bisa dibaca.
2. Normalisasi setiap baris (9.C).
3. Seluruh pemeriksaan A.2-A.7 dijalankan pada **seluruh** baris. Jangan
   berhenti di kesalahan pertama.
4. Ada >= 1 kesalahan -> berkas ditolak.

Kesalahan sejenis dikelompokkan: satu entri per kode + nilai, berisi daftar
nomor barisnya.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.konstanta import (
    BARIS_KEMBAR,
    DENDA_DIISI_NOL,
    HEADER_KOLOM_HILANG,
    HEADER_WAJIB,
    JARAK_SARAN_MAKS,
    KECAMATAN,
    KECAMATAN_TIDAK_DIKENAL,
    KELURAHAN_KE_KECAMATAN,
    KELURAHAN_TIDAK_DIKENAL,
    KOLOM_DENDA_BOLEH_KOSONG,
    KOLOM_NILAI_INTI,
    KOLOM_PENJUMLAH_TOTAL,
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
from app.services.normalisasi import (
    NilaiTidakValid,
    ke_angka,
    ke_tanggal,
    normalkan_plat,
    normalkan_wilayah,
    teks_apa_adanya,
    teks_tanggal_stnk,
)
from app.services.pembaca import BerkasExcel

__all__ = [
    "BarisBersih",
    "HasilValidasi",
    "Kesalahan",
    "Peringatan",
    "Ringkasan",
    "validasi",
]

NOL = Decimal("0")


# ---------------------------------------------------------------------------
# Bentuk hasil
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Kesalahan:
    """Satu jenis kesalahan beserta seluruh baris yang mengalaminya."""

    kode: str
    judul: str
    detail: str
    kolom: str | None
    baris: list[int]


@dataclass(frozen=True)
class Peringatan:
    """Penyesuaian otomatis; berkas tetap diterima."""

    kode: str
    pesan: str
    baris: list[int]


@dataclass
class BarisBersih:
    """Satu baris yang sudah lolos dan siap masuk ke database."""

    nomor: int

    # kunci
    no_polisi: str
    tgl_jatuh_tempo_pkb: date

    # dipakai dashboard
    kecamatan: str
    kelurahan: str
    jml_roda: int
    pkb_pokok: Decimal
    pkb_denda: Decimal
    pkb_opsen: Decimal
    pkb_denda_opsen: Decimal
    swdkllj: Decimal
    denda_swdkllj: Decimal

    # hanya untuk export, disimpan apa adanya
    nama: str
    alamat: str
    nm_kecamatan_asli: str
    nm_kelurahan_asli: str
    nm_jenis_kend: str
    nm_merk_kend: str
    th_buat: str
    warna_kend: str
    warna_tnkb_kend: str
    tgl_jatuh_tempo_stnk: str
    pnbp: Decimal
    total: Decimal | None


@dataclass
class Ringkasan:
    """Angka yang ditampilkan pada panel hijau setelah Cek File lolos."""

    baris_terbaca: int = 0
    tanggal_awal: date | None = None
    tanggal_akhir: date | None = None
    kecamatan_ada: int = 0
    kecamatan_master: int = len(KECAMATAN)
    kelurahan_ada: int = 0
    kelurahan_master: int = len(KELURAHAN_KE_KECAMATAN)


@dataclass
class HasilValidasi:
    lolos: bool
    baris: list[BarisBersih] = field(default_factory=list)
    kesalahan: list[Kesalahan] = field(default_factory=list)
    peringatan: list[Peringatan] = field(default_factory=list)
    ringkasan: Ringkasan = field(default_factory=Ringkasan)


# ---------------------------------------------------------------------------
# Pengumpul kesalahan dan peringatan
# ---------------------------------------------------------------------------


class _Pengumpul:
    """Menggabungkan kesalahan sejenis menjadi satu entri berisi daftar baris."""

    def __init__(self) -> None:
        self._entri: dict[tuple[str, str], dict] = {}

    def tambah(
        self,
        kode: str,
        kunci: str,
        judul: str,
        detail: str,
        kolom: str | None,
        nomor: int,
    ) -> None:
        simpul = self._entri.setdefault(
            (kode, kunci),
            {"judul": judul, "detail": detail, "kolom": kolom, "baris": []},
        )
        simpul["baris"].append(nomor)

    def daftar(self) -> list[Kesalahan]:
        return [
            Kesalahan(
                kode=kode,
                judul=isi["judul"],
                detail=isi["detail"],
                kolom=isi["kolom"],
                baris=sorted(set(isi["baris"])),
            )
            for (kode, _kunci), isi in self._entri.items()
        ]

    def kosong(self) -> bool:
        return not self._entri


# ---------------------------------------------------------------------------
# Saran ejaan (jarak Levenshtein)
# ---------------------------------------------------------------------------


def _jarak(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    sebelum = list(range(len(b) + 1))
    for i, huruf_a in enumerate(a, start=1):
        kini = [i]
        for j, huruf_b in enumerate(b, start=1):
            kini.append(
                min(
                    sebelum[j] + 1,          # hapus
                    kini[j - 1] + 1,          # sisip
                    sebelum[j - 1] + (huruf_a != huruf_b),  # ganti
                )
            )
        sebelum = kini
    return sebelum[-1]


def _saran(nilai: str, kandidat) -> str | None:
    """Nama master terdekat, bila jaraknya tidak lebih dari 3 huruf."""
    terbaik: str | None = None
    jarak_terbaik = JARAK_SARAN_MAKS + 1
    for nama in kandidat:
        jarak = _jarak(nilai, nama)
        if jarak < jarak_terbaik:
            terbaik, jarak_terbaik = nama, jarak
    return terbaik if jarak_terbaik <= JARAK_SARAN_MAKS else None


# ---------------------------------------------------------------------------
# Tahap header (A.1)
# ---------------------------------------------------------------------------


def _periksa_header(berkas: BerkasExcel) -> list[Kesalahan]:
    ada = set(berkas.header)
    return [
        Kesalahan(
            kode=HEADER_KOLOM_HILANG,
            judul=f'Kolom "{nama}" tidak ditemukan pada baris header',
            detail=(
                "Berkas dari pusat harus memuat ke-21 kolom baku. Periksa "
                "ejaan nama kolom pada baris pertama."
            ),
            kolom=nama,
            baris=[1],
        )
        for nama in HEADER_WAJIB
        if nama not in ada
    ]


# ---------------------------------------------------------------------------
# Pemeriksaan per baris
# ---------------------------------------------------------------------------


def _periksa_wilayah(sel, nomor, kumpul: _Pengumpul) -> tuple[str, str] | None:
    """Kembalikan (kecamatan, kelurahan) yang sah, atau None bila bermasalah."""
    kelurahan = normalkan_wilayah(sel.get("nm_kelurahan"))
    kecamatan = normalkan_wilayah(sel.get("nm_kecamatan"))
    sehat = True

    if kelurahan not in KELURAHAN_KE_KECAMATAN:
        usul = _saran(kelurahan, KELURAHAN_KE_KECAMATAN)
        detail = (
            "Nama tersebut tidak terdapat pada daftar 23 kelurahan Kota Salatiga."
        )
        if usul:
            detail += f" Apakah yang dimaksud {usul} (Kecamatan {KELURAHAN_KE_KECAMATAN[usul]})?"
        kumpul.tambah(
            KELURAHAN_TIDAK_DIKENAL,
            kelurahan,
            f'Kelurahan "{kelurahan}" tidak dikenali',
            detail,
            "nm_kelurahan",
            nomor,
        )
        sehat = False

    if kecamatan not in KECAMATAN:
        usul = _saran(kecamatan, KECAMATAN)
        detail = "Nama tersebut tidak terdapat pada daftar 4 kecamatan Kota Salatiga."
        if usul:
            detail += f" Apakah yang dimaksud {usul}?"
        kumpul.tambah(
            KECAMATAN_TIDAK_DIKENAL,
            kecamatan,
            f'Kecamatan "{kecamatan}" tidak dikenali',
            detail,
            "nm_kecamatan",
            nomor,
        )
        sehat = False

    # Pasangan hanya bermakna bila kedua nama dikenali.
    if not sehat:
        return None

    benar = KELURAHAN_KE_KECAMATAN[kelurahan]
    if benar != kecamatan:
        kumpul.tambah(
            PASANGAN_WILAYAH_SALAH,
            f"{kecamatan}|{kelurahan}",
            f"Kelurahan {kelurahan} tidak berada di Kecamatan {kecamatan}",
            f"Kelurahan {kelurahan} berada di Kecamatan {benar}, bukan {kecamatan}.",
            "nm_kelurahan",
            nomor,
        )
        return None

    return kecamatan, kelurahan


def _periksa_roda(sel, nomor, kumpul: _Pengumpul, penyesuaian) -> int | None:
    mentah = sel.get("jml_roda")
    try:
        nilai = ke_angka(mentah)
    except NilaiTidakValid:
        nilai = "salah"  # penanda; ditangani di bawah

    if nilai is None:
        kumpul.tambah(
            RODA_TIDAK_VALID,
            "",
            "Jumlah roda kosong",
            "Kolom jml_roda harus berisi bilangan bulat minimal 1.",
            "jml_roda",
            nomor,
        )
        return None

    if nilai == "salah" or nilai != nilai.to_integral_value() or nilai < 1:
        teks = teks_apa_adanya(mentah)
        kumpul.tambah(
            RODA_TIDAK_VALID,
            teks,
            f'Jumlah roda "{teks}" tidak valid',
            "Kolom jml_roda harus berisi bilangan bulat minimal 1.",
            "jml_roda",
            nomor,
        )
        return None

    roda = int(nilai)
    if roda > 4:
        penyesuaian[RODA_DIUBAH_KE_4].append(nomor)
        return 4
    if roda != 2 and roda < 4:
        penyesuaian[RODA_DIUBAH_KE_2].append(nomor)
        return 2
    return roda


def _periksa_uang(sel, nomor, kumpul: _Pengumpul, penyesuaian) -> dict | None:
    """Baca kolom uang. None bila ada yang tidak memenuhi syarat."""
    nilai: dict[str, Decimal] = {}
    sehat = True

    for kolom in KOLOM_NILAI_INTI:
        mentah = sel.get(kolom)
        try:
            angka = ke_angka(mentah)
        except NilaiTidakValid:
            teks = teks_apa_adanya(mentah)
            kumpul.tambah(
                NILAI_INTI_TIDAK_VALID,
                f"{kolom}|{teks}",
                f'{kolom} berisi "{teks}"',
                "Nilai harus berupa angka yang tidak negatif.",
                kolom,
                nomor,
            )
            sehat = False
            continue

        if angka is None:
            kumpul.tambah(
                NILAI_INTI_KOSONG,
                kolom,
                f"{kolom} kosong",
                f"Kolom {kolom} wajib terisi. Nilai 0 diperbolehkan.",
                kolom,
                nomor,
            )
            sehat = False
            continue

        if angka < 0:
            kumpul.tambah(
                NILAI_INTI_TIDAK_VALID,
                f"{kolom}|{angka}",
                f"{kolom} bernilai negatif ({angka})",
                "Nilai harus berupa angka yang tidak negatif.",
                kolom,
                nomor,
            )
            sehat = False
            continue

        nilai[kolom] = angka

    for kolom in KOLOM_DENDA_BOLEH_KOSONG:
        mentah = sel.get(kolom)
        try:
            angka = ke_angka(mentah)
        except NilaiTidakValid:
            teks = teks_apa_adanya(mentah)
            kumpul.tambah(
                NILAI_DENDA_TIDAK_VALID,
                f"{kolom}|{teks}",
                f'{kolom} berisi "{teks}"',
                "Bila terisi, nilai harus berupa angka yang tidak negatif.",
                kolom,
                nomor,
            )
            sehat = False
            continue

        if angka is None:
            penyesuaian[DENDA_DIISI_NOL].append(nomor)
            nilai[kolom] = NOL
            continue

        if angka < 0:
            kumpul.tambah(
                NILAI_DENDA_TIDAK_VALID,
                f"{kolom}|{angka}",
                f"{kolom} bernilai negatif ({angka})",
                "Bila terisi, nilai harus berupa angka yang tidak negatif.",
                kolom,
                nomor,
            )
            sehat = False
            continue

        nilai[kolom] = angka

    if not sehat:
        return None

    # TOTAL tidak divalidasi. Bila kosong atau tidak terbaca, hitung ulang
    # dari kolom 14-20.
    try:
        total = ke_angka(sel.get("TOTAL"))
    except NilaiTidakValid:
        total = None
    if total is None:
        total = sum((nilai[k] for k in KOLOM_PENJUMLAH_TOTAL), NOL)
    nilai["TOTAL"] = total

    return nilai


# ---------------------------------------------------------------------------
# Pemeriksaan lintas baris (A.7)
# ---------------------------------------------------------------------------


def _periksa_kembar(bersih: list[BarisBersih], kumpul: _Pengumpul) -> set[int]:
    """Nomor baris yang kembar. Kemiripan dinilai setelah plat dinormalkan."""
    terlihat: dict[tuple[str, date], list[int]] = {}
    for satu in bersih:
        terlihat.setdefault((satu.no_polisi, satu.tgl_jatuh_tempo_pkb), []).append(
            satu.nomor
        )

    kembar: set[int] = set()
    for (plat, tanggal), nomor_nomor in terlihat.items():
        if len(nomor_nomor) < 2:
            continue
        kembar.update(nomor_nomor)
        tampil = f"{tanggal.day:02d}/{tanggal.month:02d}/{tanggal.year:04d}"
        for nomor in nomor_nomor:
            kumpul.tambah(
                BARIS_KEMBAR,
                f"{plat}|{tampil}",
                f"Baris kembar untuk {plat} ({tampil})",
                (
                    "Satu nomor polisi hanya boleh muncul sekali untuk tanggal "
                    "jatuh tempo PKB yang sama."
                ),
                "no_polisi",
                nomor,
            )
    return kembar


# ---------------------------------------------------------------------------
# Peringatan penyesuaian otomatis (9.B)
# ---------------------------------------------------------------------------


def _susun_peringatan(penyesuaian: dict[str, list[int]]) -> list[Peringatan]:
    hasil: list[Peringatan] = []

    for kode, angka_roda in ((RODA_DIUBAH_KE_2, 2), (RODA_DIUBAH_KE_4, 4)):
        nomor_nomor = sorted(set(penyesuaian[kode]))
        if nomor_nomor:
            hasil.append(
                Peringatan(
                    kode=kode,
                    pesan=f"{len(nomor_nomor)} baris jml_roda diubah menjadi {angka_roda}",
                    baris=nomor_nomor,
                )
            )

    sel_denda = penyesuaian[DENDA_DIISI_NOL]
    if sel_denda:
        hasil.append(
            Peringatan(
                kode=DENDA_DIISI_NOL,
                # Sengaja menghitung sel, bukan baris: satu baris bisa punya
                # beberapa kolom denda yang kosong.
                pesan=f"{len(sel_denda)} sel denda/PNBP kosong diisi 0",
                baris=sorted(set(sel_denda)),
            )
        )

    return hasil


# ---------------------------------------------------------------------------
# Titik masuk
# ---------------------------------------------------------------------------


def validasi(berkas: BerkasExcel) -> HasilValidasi:
    """Jalankan seluruh pemeriksaan atas satu berkas."""
    ringkasan = Ringkasan(baris_terbaca=len(berkas.baris))

    # --- A.1: tanpa header yang benar, kolom lain tidak bisa dibaca ---
    kesalahan_header = _periksa_header(berkas)
    if kesalahan_header:
        return HasilValidasi(
            lolos=False, kesalahan=kesalahan_header, ringkasan=ringkasan
        )

    kumpul = _Pengumpul()
    penyesuaian: dict[str, list[int]] = {
        RODA_DIUBAH_KE_2: [],
        RODA_DIUBAH_KE_4: [],
        DENDA_DIISI_NOL: [],
    }
    bersih: list[BarisBersih] = []

    for baris_mentah in berkas.baris:
        nomor, sel = baris_mentah.nomor, baris_mentah.sel
        sehat = True

        # A.3 nomor polisi
        plat = normalkan_plat(sel.get("no_polisi"))
        if not plat:
            kumpul.tambah(
                PLAT_KOSONG,
                "",
                "Nomor polisi kosong",
                "Kolom no_polisi wajib terisi.",
                "no_polisi",
                nomor,
            )
            sehat = False

        # A.4 tanggal jatuh tempo PKB
        jatuh_tempo: date | None = None
        mentah_tanggal = sel.get("tgl_jatuh_tempo_pkb")
        try:
            jatuh_tempo = ke_tanggal(mentah_tanggal)
        except NilaiTidakValid:
            teks = teks_apa_adanya(mentah_tanggal)
            kumpul.tambah(
                TANGGAL_TIDAK_VALID,
                teks,
                f'Tanggal "{teks}" tidak valid',
                "Gunakan format dd/mm/yyyy.",
                "tgl_jatuh_tempo_pkb",
                nomor,
            )
            sehat = False
        else:
            if jatuh_tempo is None:
                kumpul.tambah(
                    TANGGAL_KOSONG,
                    "",
                    "Tanggal jatuh tempo PKB kosong",
                    "Kolom tgl_jatuh_tempo_pkb wajib terisi.",
                    "tgl_jatuh_tempo_pkb",
                    nomor,
                )
                sehat = False

        # A.2 wilayah
        wilayah = _periksa_wilayah(sel, nomor, kumpul)
        if wilayah is None:
            sehat = False

        # A.5 jumlah roda
        roda = _periksa_roda(sel, nomor, kumpul, penyesuaian)
        if roda is None:
            sehat = False

        # A.6 kolom uang
        uang = _periksa_uang(sel, nomor, kumpul, penyesuaian)
        if uang is None:
            sehat = False

        if not sehat:
            continue

        kecamatan, kelurahan = wilayah
        bersih.append(
            BarisBersih(
                nomor=nomor,
                no_polisi=plat,
                tgl_jatuh_tempo_pkb=jatuh_tempo,
                kecamatan=kecamatan,
                kelurahan=kelurahan,
                jml_roda=roda,
                pkb_pokok=uang["PKB Pokok"],
                pkb_denda=uang["PKB Denda"],
                pkb_opsen=uang["PKB Opsen"],
                pkb_denda_opsen=uang["PKB Denda Opsen"],
                swdkllj=uang["SWDKLLJ"],
                denda_swdkllj=uang["Denda SWDKLLJ"],
                nama=teks_apa_adanya(sel.get("nama")),
                alamat=teks_apa_adanya(sel.get("alamat")),
                nm_kecamatan_asli=teks_apa_adanya(sel.get("nm_kecamatan")),
                nm_kelurahan_asli=teks_apa_adanya(sel.get("nm_kelurahan")),
                nm_jenis_kend=teks_apa_adanya(sel.get("nm_jenis_kend")),
                nm_merk_kend=teks_apa_adanya(sel.get("nm_merk_kend")),
                th_buat=teks_apa_adanya(sel.get("th_buat")),
                warna_kend=teks_apa_adanya(sel.get("warna_kend")),
                warna_tnkb_kend=teks_apa_adanya(sel.get("warna_tnkb_kend")),
                tgl_jatuh_tempo_stnk=teks_tanggal_stnk(sel.get("tgl_jatuh_tempo_stnk")),
                pnbp=uang["PNBP"],
                total=uang["TOTAL"],
            )
        )

    # --- A.7: kembar di dalam satu berkas ---
    kembar = _periksa_kembar(bersih, kumpul)
    if kembar:
        bersih = [satu for satu in bersih if satu.nomor not in kembar]

    kesalahan = kumpul.daftar()
    lolos = not kesalahan

    if bersih:
        tanggal_tanggal = [satu.tgl_jatuh_tempo_pkb for satu in bersih]
        ringkasan.tanggal_awal = min(tanggal_tanggal)
        ringkasan.tanggal_akhir = max(tanggal_tanggal)
        ringkasan.kecamatan_ada = len({satu.kecamatan for satu in bersih})
        ringkasan.kelurahan_ada = len({satu.kelurahan for satu in bersih})

    return HasilValidasi(
        lolos=lolos,
        baris=bersih if lolos else [],
        kesalahan=kesalahan,
        peringatan=_susun_peringatan(penyesuaian) if lolos else [],
        ringkasan=ringkasan,
    )
