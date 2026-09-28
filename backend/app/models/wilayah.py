"""Akses data tabel ``dim_wilayah``. SQL mentah, tanpa ORM."""

from app.database import ambil_semua

__all__ = ["dikelompokkan", "semua"]

def semua() -> list[dict]:
    return ambil_semua(
        """
        SELECT id, kecamatan, kelurahan FROM dim_wilayah
        ORDER BY kecamatan, kelurahan
        """
    )

def dikelompokkan() -> list[dict]:
    """[{kecamatan, kelurahan: [...]}] untuk mengisi pilihan filter."""
    kelompok: dict[str, list[str]] = {}
    for baris in semua():
        kelompok.setdefault(baris["kecamatan"], []).append(baris["kelurahan"])
    return [
        {"kecamatan": kecamatan, "kelurahan": kelurahan}
        for kecamatan, kelurahan in kelompok.items()
    ]
