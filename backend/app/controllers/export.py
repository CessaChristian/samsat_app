"""Controller /api/export.xlsx dan /api/export.pdf.

Isi kedua berkas sama — seluruh baris detail yang lolos filter aktif — jadi
kedua rute memakai filter yang sama persis dengan /api/rekap. Dengan begitu
angka di layar dan isi berkas tidak pernah berbeda.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 11 (Export) dan 13.
"""

from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required

from app.services import export_pdf, export_xlsx
from app.services.rekap import FilterTidakValid, buat_filter

bp = Blueprint("export", __name__, url_prefix="/api")

TIPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _kirim(tulis, tipe: str, akhiran: str):
    """Susun berkas lalu kirim sebagai unduhan bernama periode filternya."""
    try:
        saringan = buat_filter(request.args)
    except FilterTidakValid as exc:
        return jsonify({"kode": "FILTER_TIDAK_VALID", "pesan": str(exc)}), 400

    return send_file(
        tulis(saringan),
        mimetype=tipe,
        as_attachment=True,
        download_name=f"rekap-pkb_{saringan.dari}_{saringan.sampai}.{akhiran}",
    )


@bp.get("/export.xlsx")
@login_required
def excel():
    return _kirim(export_xlsx.tulis, TIPE_XLSX, "xlsx")


@bp.get("/export.pdf")
@login_required
def pdf():
    return _kirim(export_pdf.tulis, "application/pdf", "pdf")
