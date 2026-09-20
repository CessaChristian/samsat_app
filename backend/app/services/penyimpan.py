"""Menyimpan satu berkas unggahan ke database dalam **satu transaksi**.

Gagal di tengah berarti tidak ada yang tersimpan sama sekali; data lama tetap
utuh. Tidak ada baris yang dihapus — riwayat periode terbentuk sendiri dari
akumulasi baris.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 6, 7.1, dan 10.3.
"""

from dataclasses import dataclass
from typing import Sequence

from psycopg.types.json import Json

from app.database import koneksi, muat_sql
from app.services.validator import BarisBersih

__all__ = ["HasilSimpan", "WilayahTidakDikenal", "simpan"]

#: Urutan kolom saat COPY ke tabel staging. Harus sama dengan staging_buat.sql.
_KOLOM_STAGING = (
    "no_polisi",
    "tgl_jatuh_tempo_pkb",
    "wilayah_id",
    "jml_roda",
    "pkb_pokok",
    "pkb_denda",
    "pkb_opsen",
    "pkb_denda_opsen",
    "swdkllj",
    "denda_swdkllj",
    "nama",
    "alamat",
    "nm_kecamatan_asli",
    "nm_kelurahan_asli",
    "nm_jenis_kend",
    "nm_merk_kend",
    "th_buat",
    "warna_kend",
    "warna_tnkb_kend",
    "tgl_jatuh_tempo_stnk",
    "pnbp",
    "total",
)


class WilayahTidakDikenal(Exception):
    """Kelurahan pada baris tidak ada di master ``dim_wilayah``.

    Seharusnya sudah tersaring validator; bila sampai ke sini berarti master
    wilayah dan berkas tidak sejalan, dan penyimpanan dibatalkan.
    """


@dataclass(frozen=True)
class HasilSimpan:
    batch_id: int
    jumlah_baris: int
    baris_baru: int
    baris_diperbarui: int


def _peta_wilayah(cur) -> dict[str, int]:
    cur.execute("SELECT kelurahan, id FROM dim_wilayah")
    return {b["kelurahan"]: b["id"] for b in cur.fetchall()}


def simpan(
    baris: Sequence[BarisBersih],
    *,
    nama_file: str,
    hash_file: str,
    ukuran_byte: int,
    peringatan: list[dict] | None = None,
) -> HasilSimpan:
    """Simpan seluruh baris yang sudah lolos validasi.

    Mengembalikan jumlah baris baru dan baris yang diperbarui, dihitung
    sebelum upsert dijalankan.
    """
    if not baris:
        raise ValueError("Tidak ada baris untuk disimpan.")

    with koneksi() as conn, conn.cursor() as cur:
        # Satu transaksi untuk seluruh blok ini: pool mengembalikan koneksi
        # tanpa autocommit, dan ON COMMIT DROP membersihkan tabel sementara.
        cur.execute(muat_sql("staging_buat.sql"))

        peta = _peta_wilayah(cur)
        tidak_dikenal = sorted(
            {satu.kelurahan for satu in baris if satu.kelurahan not in peta}
        )
        if tidak_dikenal:
            raise WilayahTidakDikenal(
                "Kelurahan berikut tidak ada di master dim_wilayah: "
                + ", ".join(tidak_dikenal)
            )

        perintah_copy = f"COPY staging ({', '.join(_KOLOM_STAGING)}) FROM STDIN"
        with cur.copy(perintah_copy) as salin:
            for satu in baris:
                salin.write_row(
                    (
                        satu.no_polisi,
                        satu.tgl_jatuh_tempo_pkb,
                        peta[satu.kelurahan],
                        satu.jml_roda,
                        satu.pkb_pokok,
                        satu.pkb_denda,
                        satu.pkb_opsen,
                        satu.pkb_denda_opsen,
                        satu.swdkllj,
                        satu.denda_swdkllj,
                        satu.nama,
                        satu.alamat,
                        satu.nm_kecamatan_asli,
                        satu.nm_kelurahan_asli,
                        satu.nm_jenis_kend,
                        satu.nm_merk_kend,
                        satu.th_buat,
                        satu.warna_kend,
                        satu.warna_tnkb_kend,
                        satu.tgl_jatuh_tempo_stnk,
                        satu.pnbp,
                        satu.total,
                    )
                )

        # Dihitung sebelum upsert, selagi baris lama dan baru masih terbedakan.
        cur.execute(muat_sql("hitung_baris_diperbarui.sql"))
        diperbarui = cur.fetchone()["jumlah"]
        jumlah = len(baris)
        baru = jumlah - diperbarui

        cur.execute(
            """
            INSERT INTO ingest_batch (
                nama_file, hash_file, ukuran_byte,
                jumlah_baris, baris_baru, baris_diperbarui, peringatan
            ) VALUES (
                %(nama_file)s, %(hash_file)s, %(ukuran_byte)s,
                %(jumlah_baris)s, %(baris_baru)s, %(baris_diperbarui)s, %(peringatan)s
            ) RETURNING id
            """,
            {
                "nama_file": nama_file,
                "hash_file": hash_file,
                "ukuran_byte": ukuran_byte,
                "jumlah_baris": jumlah,
                "baris_baru": baru,
                "baris_diperbarui": diperbarui,
                "peringatan": Json(peringatan or []),
            },
        )
        batch_id = cur.fetchone()["id"]

        cur.execute(muat_sql("upsert_kewajiban.sql"), {"batch_id": batch_id})
        cur.execute(muat_sql("hitung_ulang_lunas.sql"))

    return HasilSimpan(
        batch_id=batch_id,
        jumlah_baris=jumlah,
        baris_baru=baru,
        baris_diperbarui=diperbarui,
    )
