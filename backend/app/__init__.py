"""Pabrik aplikasi Flask.
"""

from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from werkzeug.exceptions import RequestEntityTooLarge

from app.config import Config
from app.konstanta import BERKAS_TERLALU_BESAR
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


PESAN_BELUM_DIBANGUN = (
    "Tampilan belum dibangun.\n\n"
    "Jalankan sekali di folder frontend:\n\n"
    "    npm install\n"
    "    npm run build\n\n"
    "lalu muat ulang halaman ini. API di /api tetap berjalan."
)


def _pasang_tampilan(app: Flask, folder: Path) -> None:
    """Sajikan hasil build frontend di akar situs.

    Dengan begini ``python3 main.py`` saja sudah melayani tampilan sekaligus
    API di alamat yang sama, jadi saat demo tidak perlu menyalakan Vite.
    Berkas pendukung (/assets, /favicon.svg) ditangani penyajian statis
    bawaan Flask; yang perlu rute tersendiri hanya halaman utamanya.
    """

    @app.get("/")
    def halaman_utama():
        if not (folder / "index.html").is_file():
            return (
                PESAN_BELUM_DIBANGUN,
                503,
                {"Content-Type": "text/plain; charset=utf-8"},
            )
        return send_from_directory(folder, "index.html")


def _pasang_penangan_galat(app: Flask) -> None:
    """Balas JSON untuk galat yang ditimbulkan Flask sendiri.

    MAX_CONTENT_LENGTH ditegakkan Flask saat membaca badan permintaan,
    yaitu sebelum controller dijalankan. Tanpa penangan ini balasannya
    halaman HTML bawaan yang tidak bisa dibaca frontend.
    """

    @app.errorhandler(RequestEntityTooLarge)
    def terlalu_besar(_):
        batas = app.config["MAX_CONTENT_LENGTH"]
        return (
            jsonify(
                {
                    "kode": BERKAS_TERLALU_BESAR,
                    "pesan": f"Berkas melebihi batas {batas // (1024 * 1024)} MB.",
                }
            ),
            413,
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
        # Berkas export memuat nama dan alamat juga. send_file memasang
        # Cache-Control sendiri, jadi di sini nilainya ditimpa, bukan
        # sekadar diisi bila kosong.
        unduhan = "attachment" in balasan.headers.get("Content-Disposition", "")
        if balasan.mimetype == "application/json" or unduhan:
            balasan.headers["Cache-Control"] = "no-store"
        return balasan


def create_app(config_object: type[Config] = Config) -> Flask:
    """Rakit aplikasi: konfigurasi, ekstensi, lalu controller."""
    folder_tampilan = Path(config_object.FOLDER_FRONTEND)
    # static_url_path kosong: berkas build tersaji di akar, persis seperti
    # rujukan di dalam index.html ("/assets/...", "/favicon.svg").
    app = Flask(__name__, static_folder=str(folder_tampilan), static_url_path="")
    app.config.from_object(config_object)
    config_object.periksa()

    # Urutan kunci JSON mengikuti urutan penulisan, bukan abjad, supaya
    # balasannya terbaca serupa dengan yang tertulis di kode.
    app.json.sort_keys = False

    login_manager.init_app(app)
    _pasang_penangan_galat(app)
    _pasang_header_keamanan(app)
    _pasang_tampilan(app, folder_tampilan)

    from app.controllers import auth, export, meta, rekap, upload

    app.register_blueprint(auth.bp)
    app.register_blueprint(upload.bp)
    app.register_blueprint(meta.bp)
    app.register_blueprint(rekap.bp)
    app.register_blueprint(export.bp)

    return app
