"""Akses data tabel ``ingest_batch``. SQL mentah, tanpa ORM."""

from app.database import ambil_satu

__all__ = ["terakhir", "terakhir_dengan_hash"]


def terakhir_dengan_hash(hash_file: str) -> dict | None:
    """Batch terakhir yang berkasnya persis sama isinya.

    Hash sengaja tidak unik: berkas yang sama boleh disimpan ulang, hanya
    diberi peringatan (bagian 9.B).
    """
    return ambil_satu(
        "SELECT id, nama_file, disimpan_pada FROM ingest_batch"
        " WHERE hash_file = %s ORDER BY disimpan_pada DESC, id DESC LIMIT 1",
        (hash_file,),
    )


def terakhir() -> dict | None:
    """Batch paling akhir, untuk tulisan "Data per <tanggal>" di header."""
    return ambil_satu(
        "SELECT id, nama_file, disimpan_pada, jumlah_baris FROM ingest_batch"
        " ORDER BY disimpan_pada DESC, id DESC LIMIT 1"
    )
