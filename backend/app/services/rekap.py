"""Perhitungan seluruh angka dashboard.

Semua perhitungan hanya memakai baris dengan ``tgl_jatuh_tempo_pkb`` di dalam
periode, dan periode tidak pernah melewati ``hari_ini()``. Baris dengan jatuh
tempo di masa depan hanya berfungsi sebagai penanda lunas.

**Opsen tidak pernah dihitung dari PKB.** Nilainya selalu diambil dari data.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 7.2 dan 12.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Mapping

from app.database import ambil_satu, ambil_semua, muat_sql
from app.konstanta import KECAMATAN, KELURAHAN_KE_KECAMATAN
from app.utils.waktu import hari_ini

__all__ = ["Filter", "FilterTidakValid", "buat_filter", "hitung", "rentang_tersedia"]

RODA_SAH = (2, 4)
STATUS_SAH = ("LUNAS", "BELUM_LUNAS")


class FilterTidakValid(ValueError):
    """Nilai filter dari klien tidak masuk akal."""


@dataclass(frozen=True)
class Filter:
    dari: date
    sampai: date
    roda: int | None = None
    lunas: bool | None = None
    kecamatan: str | None = None
    kelurahan: str | None = None

    def params(self) -> dict:
        return {
            "dari": self.dari,
            "sampai": self.sampai,
            "roda": self.roda,
            "lunas": self.lunas,
            "kecamatan": self.kecamatan,
            "kelurahan": self.kelurahan,
        }


def rentang_tersedia() -> tuple[date | None, date | None, int]:
    """(awal, akhir, jumlah baris). ``akhir`` dipotong di hari ini."""
    baris = ambil_satu(muat_sql("rentang_periode.sql"))
    if not baris or not baris["jumlah"]:
        return None, None, 0
    batas = hari_ini()
    akhir = min(baris["akhir"], batas) if baris["akhir"] else None
    return baris["awal"], akhir, baris["jumlah"]


def _tanggal(nilai: str, nama: str) -> date:
    try:
        return date.fromisoformat(nilai)
    except ValueError as exc:
        raise FilterTidakValid(
            f'Parameter "{nama}" harus berformat YYYY-MM-DD, bukan "{nilai}".'
        ) from exc


def buat_filter(args: Mapping[str, str]) -> Filter:
    """Susun filter dari query string. Seluruh parameter opsional."""
    batas = hari_ini()
    awal_data, akhir_data, jumlah = rentang_tersedia()
    if not jumlah:
        awal_data = akhir_data = batas

    teks_dari = (args.get("dari") or "").strip()
    teks_sampai = (args.get("sampai") or "").strip()
    dari = _tanggal(teks_dari, "dari") if teks_dari else awal_data
    sampai = _tanggal(teks_sampai, "sampai") if teks_sampai else akhir_data

    # Bagian 11: "sampai" yang melewati hari ini dipotong menjadi hari ini.
    sampai = min(sampai, batas)
    if dari > sampai:
        dari = sampai

    roda: int | None = None
    teks_roda = (args.get("roda") or "").strip()
    if teks_roda:
        if not teks_roda.isdigit() or int(teks_roda) not in RODA_SAH:
            raise FilterTidakValid('Parameter "roda" hanya boleh 2 atau 4.')
        roda = int(teks_roda)

    lunas: bool | None = None
    teks_status = (args.get("status") or "").strip().upper()
    if teks_status:
        if teks_status not in STATUS_SAH:
            raise FilterTidakValid(
                'Parameter "status" hanya boleh LUNAS atau BELUM_LUNAS.'
            )
        lunas = teks_status == "LUNAS"

    kecamatan = (args.get("kecamatan") or "").strip().upper() or None
    if kecamatan and kecamatan not in KECAMATAN:
        raise FilterTidakValid(f'Kecamatan "{kecamatan}" tidak dikenali.')

    kelurahan = (args.get("kelurahan") or "").strip().upper() or None
    if kelurahan and kelurahan not in KELURAHAN_KE_KECAMATAN:
        raise FilterTidakValid(f'Kelurahan "{kelurahan}" tidak dikenali.')

    return Filter(
        dari=dari,
        sampai=sampai,
        roda=roda,
        lunas=lunas,
        kecamatan=kecamatan,
        kelurahan=kelurahan,
    )


def _rupiah(nilai) -> int:
    """Uang dikirim sebagai angka bulat rupiah; pemformatan urusan frontend."""
    return int(nilai or 0)


def _persen(bagian: int, keseluruhan: int) -> float:
    if not keseluruhan:
        return 0.0
    return round(bagian / keseluruhan * 100, 1)


def hitung(f: Filter) -> dict:
    """Seluruh isi dashboard untuk satu kombinasi filter."""
    params = f.params()

    per_wilayah = ambil_semua(muat_sql("rekap_per_wilayah.sql"), params)
    per_kecamatan = ambil_semua(muat_sql("rekap_per_kecamatan.sql"), params)
    komposisi = ambil_semua(muat_sql("rekap_komposisi.sql"), params)
    periode = ambil_satu(
        muat_sql("rekap_objek_periode.sql"), {"dari": f.dari, "sampai": f.sampai}
    )

    objek_total = sum(b["objek"] for b in per_wilayah)
    pkb_total = sum(b["pkb"] for b in per_wilayah)
    opsen_total = sum(b["opsen_pkb"] for b in per_wilayah)
    swdkllj_total = sum(b["swdkllj"] for b in per_wilayah)

    objek_periode = periode["objek"] if periode else 0
    hitung_roda = {b["roda"]: b["objek"] for b in komposisi}

    return {
        "periode": {"dari": f.dari.isoformat(), "sampai": f.sampai.isoformat()},
        "kpi": {
            "objek": objek_total,
            "pkb": _rupiah(pkb_total),
            "opsen_pkb": _rupiah(opsen_total),
            "swdkllj": _rupiah(swdkllj_total),
        },
        "persentase": {
            "objek_filter": objek_total,
            "objek_periode": objek_periode,
            "persen": _persen(objek_total, objek_periode),
        },
        # Kedua nilai roda selalu hadir supaya donut tidak berubah bentuk.
        "komposisi": [
            {"roda": roda, "objek": hitung_roda.get(roda, 0)} for roda in RODA_SAH
        ],
        "per_kecamatan": [
            {"kecamatan": b["kecamatan"], "pkb": _rupiah(b["pkb"])}
            for b in per_kecamatan
        ],
        "per_wilayah": [
            {
                "kecamatan": b["kecamatan"],
                "kelurahan": b["kelurahan"],
                "objek": b["objek"],
                "persen": _persen(b["objek"], objek_total),
                "pkb": _rupiah(b["pkb"]),
                "opsen_pkb": _rupiah(b["opsen_pkb"]),
                "swdkllj": _rupiah(b["swdkllj"]),
            }
            for b in per_wilayah
        ],
        "total": {
            "objek": objek_total,
            "persen": _persen(objek_total, objek_total) if objek_total else 0.0,
            "pkb": _rupiah(pkb_total),
            "opsen_pkb": _rupiah(opsen_total),
            "swdkllj": _rupiah(swdkllj_total),
        },
    }
