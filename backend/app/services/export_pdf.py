"""Export PDF.

ReportLab ``LongTable`` di kertas A3 landscape, huruf 6 pt, header tabel
diulang di setiap halaman, nomor halaman di kaki.

Berbeda dengan export Excel, seluruh baris harus ditampung lebih dulu karena
``LongTable`` menghitung tinggi tiap baris sebelum memecah halaman. Untuk
data sebesar berkas pusat hal ini masih wajar; PDF yang sampai ratusan
halaman memang diterima.
"""

import io
from datetime import date, datetime
from decimal import Decimal
from typing import Iterator, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle

from app.konstanta import HEADER_WAJIB
from app.models import kewajiban as model_kewajiban
from app.services.export import KOLOM_UANG, PETA_KOLOM

#: Bobot lebar tiap kolom, dibagi rata terhadap lebar kertas yang tersisa.
#: Kolom teks panjang (nama, alamat) diberi porsi terbesar.
BOBOT_KOLOM: dict[str, int] = {
    "no_polisi": 3,
    "nama": 6,
    "alamat": 7,
    "nm_kecamatan": 4,
    "nm_kelurahan": 6,
    "nm_jenis_kend": 6,
    "nm_merk_kend": 4,
    "th_buat": 2,
    "warna_kend": 5,
    "warna_tnkb_kend": 4,
    "jml_roda": 2,
    "tgl_jatuh_tempo_pkb": 4,
    "tgl_jatuh_tempo_stnk": 4,
}
BOBOT_UANG = 4

UKURAN_HURUF = 6
HURUF_JUDUL = "Helvetica-Bold"
HURUF_ISI = "Helvetica"
PADDING = 2
MARGIN = 10 * mm

#: Kolom uang berada di 8 posisi terakhir; dipakai untuk rata kanan.
AWAL_KOLOM_UANG = len(HEADER_WAJIB) - len(KOLOM_UANG)


# --- isi -------------------------------------------------------------------


def _angka(nilai) -> str:
    """1234567 -> "1.234.567". Uang selalu bulat rupiah."""
    return f"{int(Decimal(nilai)):,}".replace(",", ".")


def _teks(header: str, baris: dict) -> str:
    nilai = baris[PETA_KOLOM[header]]
    if nilai is None:
        return ""
    if header in KOLOM_UANG:
        return _angka(nilai)
    if isinstance(nilai, date):
        return nilai.strftime("%d/%m/%Y")
    return str(nilai)


def baris_tabel(saringan) -> Iterator[list[str]]:
    """Header lalu tiap baris detail, semuanya sebagai teks siap cetak."""
    yield list(HEADER_WAJIB)
    for baris in model_kewajiban.detail(saringan):
        yield [_teks(header, baris) for header in HEADER_WAJIB]


def rincian_filter(saringan) -> str:
    """Filter aktif dalam satu baris, untuk dicetak di kepala halaman."""
    bagian: list[str] = []
    if saringan.roda:
        bagian.append(f"Roda {saringan.roda}")
    if saringan.lunas is not None:
        bagian.append("Lunas" if saringan.lunas else "Belum lunas")
    if saringan.kecamatan:
        bagian.append(f"Kecamatan {saringan.kecamatan}")
    if saringan.kelurahan:
        bagian.append(f"Kelurahan {saringan.kelurahan}")
    return " · ".join(bagian) if bagian else "Semua data"


def baris_judul(saringan, dicetak: datetime) -> list[str]:
    """Empat baris kepala halaman pertama."""
    return [
        "Rekapitulasi PKB — Samsat Kota Salatiga",
        f"Periode {saringan.dari:%d/%m/%Y} – {saringan.sampai:%d/%m/%Y}"
        " (jatuh tempo setelah hari ini tidak ikut dihitung)",
        f"Filter: {rincian_filter(saringan)}",
        f"Dicetak {dicetak:%d/%m/%Y %H:%M}",
    ]


# --- bentuk ----------------------------------------------------------------


def lebar_kolom(tersedia: float) -> list[float]:
    """Lebar tiap kolom dalam poin, sebanding dengan bobotnya."""
    bobot = [BOBOT_KOLOM.get(header, BOBOT_UANG) for header in HEADER_WAJIB]
    jumlah = sum(bobot)
    return [tersedia * satu / jumlah for satu in bobot]


def pecah_teks(teks: str, lebar: float, huruf: str) -> str:
    """Pecah teks menjadi beberapa baris agar muat selebar kolomnya.

    Judul seperti ``tgl_jatuh_tempo_stnk`` dan isi seperti alamat lebih lebar
    daripada kolomnya, dan akan menimpa kolom sebelahnya bila ditulis satu
    baris. Pemotongan diutamakan tepat setelah spasi atau garis bawah supaya
    masih terbaca; bila satu penggal pun masih kelebaran, barulah dipotong
    per huruf. Tidak ada isi yang dibuang.
    """
    muat = lebar - 2 * PADDING
    if stringWidth(teks, huruf, UKURAN_HURUF) <= muat:
        return teks

    # Penggal berakhir tepat setelah garis bawah atau spasi, supaya pemotongan
    # jatuh di batas kata: "PKB Denda" + "Opsen", bukan "PKB Denda Ops" + "en".
    penggal: list[str] = []
    sekarang = ""
    for aksara in teks:
        sekarang += aksara
        if aksara in "_ ":
            penggal.append(sekarang)
            sekarang = ""
    if sekarang:
        penggal.append(sekarang)

    baris: list[str] = []
    sekarang = ""
    for satu in penggal:
        calon = sekarang + satu
        if sekarang and stringWidth(calon, huruf, UKURAN_HURUF) > muat:
            baris.append(sekarang)
            sekarang = satu
        else:
            sekarang = calon
    baris.append(sekarang)

    # Satu penggal yang tetap kelebaran dipotong per huruf.
    hasil: list[str] = []
    for satu in baris:
        while stringWidth(satu, huruf, UKURAN_HURUF) > muat and len(satu) > 1:
            potong = len(satu) - 1
            while potong > 1 and stringWidth(satu[:potong], huruf, UKURAN_HURUF) > muat:
                potong -= 1
            hasil.append(satu[:potong])
            satu = satu[potong:]
        hasil.append(satu)

    return "\n".join(baris.rstrip() for baris in hasil)


def pecah_judul(teks: str, lebar: float) -> str:
    """Judul kolom memakai huruf tebal, jadi lebarnya dihitung berbeda."""
    return pecah_teks(teks, lebar, HURUF_JUDUL)


def tabel(data: Sequence[Sequence[str]], tersedia: float) -> LongTable:
    """LongTable siap cetak: header diulang, huruf kecil, garis tipis."""
    lebar = lebar_kolom(tersedia)
    isi = [
        [pecah_judul(judul, satu) for judul, satu in zip(data[0], lebar)],
        *(
            [pecah_teks(sel, satu, HURUF_ISI) for sel, satu in zip(baris, lebar)]
            for baris in data[1:]
        ),
    ]
    hasil = LongTable(isi, colWidths=lebar, repeatRows=1)
    hasil.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), HURUF_JUDUL),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), UKURAN_HURUF),
                ("LEADING", (0, 0), (-1, -1), UKURAN_HURUF + 1.5),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E7EDF7")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BCC6D6")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (AWAL_KOLOM_UANG, 0), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), PADDING),
                ("RIGHTPADDING", (0, 0), (-1, -1), PADDING),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ]
        )
    )
    return hasil


def _kaki(kanvas, dokumen) -> None:
    kanvas.saveState()
    kanvas.setFont("Helvetica", 7)
    kanvas.setFillColor(colors.HexColor("#5A6472"))
    kanvas.drawRightString(
        dokumen.pagesize[0] - MARGIN, 7 * mm, f"Halaman {kanvas.getPageNumber()}"
    )
    kanvas.restoreState()


def tulis(saringan, dicetak: datetime | None = None) -> io.BytesIO:
    """Susun berkas .pdf berisi baris yang lolos ``saringan``."""
    dicetak = dicetak or datetime.now()
    keluaran = io.BytesIO()

    dokumen = SimpleDocTemplate(
        keluaran,
        pagesize=landscape(A3),
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=12 * mm,
        title="Rekapitulasi PKB — Samsat Kota Salatiga",
    )

    gaya_judul = ParagraphStyle("judul", fontName="Helvetica-Bold", fontSize=11, leading=14)
    gaya_keterangan = ParagraphStyle("ket", fontName="Helvetica", fontSize=7.5, leading=10)

    judul, *keterangan = baris_judul(saringan, dicetak)
    cerita = [Paragraph(judul, gaya_judul)]
    cerita += [Paragraph(satu, gaya_keterangan) for satu in keterangan]
    cerita.append(Spacer(1, 6))
    cerita.append(tabel(list(baris_tabel(saringan)), dokumen.width))

    dokumen.build(cerita, onFirstPage=_kaki, onLaterPages=_kaki)
    keluaran.seek(0)
    return keluaran
