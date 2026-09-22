"""Pabrik aplikasi Flask.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 15.
"""

from flask import Flask

from app.config import Config
from app.extensions import login_manager

#: Aplikasi hanya memuat skripnya sendiri; satu-satunya pihak luar adalah
#: Google Fonts (lembar gaya dan berkas hurufnya). "unsafe-inline" pada style
#: diperlukan karena komponen React memakai atribut style sebaris.
KEBIJAKAN_KEAMANAN_KONTEN = "; ".join(
    (
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data:",
        "connect-src 'self'",
        "form-action 'self'",
        "base-uri 'self'",
        "frame-ancestors 'none'",
        "object-src 'none'",
    )
)


def _pasang_header_keamanan(app: Flask) -> None:
    """Header yang berlaku untuk seluruh respons.

    Balasan API memuat nama dan alamat pemilik kendaraan, jadi tidak boleh
    disimpan di cache peramban atau proxy, dan halaman tidak boleh disematkan
    di situs lain.
    """

    @app.after_request
    def tambahkan(balasan):
        balasan.headers.setdefault("X-Content-Type-Options", "nosniff")
        balasan.headers.setdefault("X-Frame-Options", "DENY")
        balasan.headers.setdefault("Referrer-Policy", "no-referrer")
        balasan.headers.setdefault(
            "Content-Security-Policy", KEBIJAKAN_KEAMANAN_KONTEN
        )
        if balasan.mimetype == "application/json":
            balasan.headers.setdefault("Cache-Control", "no-store")
        return balasan


def create_app(config_object: type[Config] = Config) -> Flask:
    """Rakit aplikasi: konfigurasi, ekstensi, lalu controller."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    config_object.periksa()

    login_manager.init_app(app)
    _pasang_header_keamanan(app)

    from app.controllers import auth, meta, rekap, upload

    app.register_blueprint(auth.bp)
    app.register_blueprint(upload.bp)
    app.register_blueprint(meta.bp)
    app.register_blueprint(rekap.bp)

    return app
