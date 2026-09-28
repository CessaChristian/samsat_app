"""Controller /api/rekap: satu respons untuk seluruh isi dashboard.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.services.rekap import FilterTidakValid, buat_filter, hitung

bp = Blueprint("rekap", __name__, url_prefix="/api")

@bp.get("/rekap")
@login_required
def rekap():
    try:
        saringan = buat_filter(request.args)
    except FilterTidakValid as exc:
        return jsonify({"kode": "FILTER_TIDAK_VALID", "pesan": str(exc)}), 400

    return jsonify(hitung(saringan))
