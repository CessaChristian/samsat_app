"""Controller autentikasi: /api/auth/login, /logout, /me.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 11 (Auth) dan 14 (Login).
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from app.models.pengguna import Pengguna, ambil_per_username

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return (
            jsonify(
                {
                    "kode": "KREDENSIAL_TIDAK_LENGKAP",
                    "pesan": "Username dan kata sandi wajib diisi.",
                }
            ),
            400,
        )

    baris = ambil_per_username(username)
    # Pesan sengaja seragam supaya tidak terungkap username mana yang terdaftar.
    if not baris or not check_password_hash(baris["password_hash"], password):
        return (
            jsonify({"kode": "LOGIN_GAGAL", "pesan": "Username atau kata sandi salah."}),
            401,
        )

    login_user(Pengguna.dari_baris(baris), remember=False)
    return jsonify({"username": baris["username"]})


@bp.post("/logout")
def logout():
    logout_user()
    return "", 204


@bp.get("/me")
@login_required
def me():
    return jsonify({"username": current_user.username})
