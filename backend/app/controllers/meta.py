"""Controller /api/meta: keterangan yang dibutuhkan dashboard saat dimuat.
"""

from flask import Blueprint, jsonify
from flask_login import login_required

from app.models import batch as model_batch
from app.models import wilayah as model_wilayah
from app.services.rekap import RODA_SAH, STATUS_SAH, rentang_tersedia

bp = Blueprint("meta", __name__, url_prefix="/api")

@bp.get("/meta")
@login_required
def meta():
    awal, akhir, jumlah = rentang_tersedia()
    terakhir = model_batch.terakhir()

    return jsonify(
        {
            "ada_data": jumlah > 0,
            "periode": {
                "awal": awal.isoformat() if awal else None,
                "akhir": akhir.isoformat() if akhir else None,
            },
            "batch_terakhir": (
                {
                    "nama_file": terakhir["nama_file"],
                    "disimpan_pada": terakhir["disimpan_pada"].isoformat(),
                    "jumlah_baris": terakhir["jumlah_baris"],
                }
                if terakhir
                else None
            ),
            "wilayah": model_wilayah.dikelompokkan(),
            "opsi": {"roda": list(RODA_SAH), "status": list(STATUS_SAH)},
        }
    )
