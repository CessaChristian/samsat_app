"""Pabrik aplikasi Flask.

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 15.
"""

from flask import Flask

from app.config import Config
from app.extensions import login_manager


def create_app(config_object: type[Config] = Config) -> Flask:
    """Rakit aplikasi: konfigurasi, ekstensi, lalu controller."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    config_object.periksa()

    login_manager.init_app(app)

    from app.controllers import auth, meta, rekap, upload

    app.register_blueprint(auth.bp)
    app.register_blueprint(upload.bp)
    app.register_blueprint(meta.bp)
    app.register_blueprint(rekap.bp)

    return app
