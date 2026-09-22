"""Tes header keamanan HTTP.

Balasan API memuat nama dan alamat pemilik kendaraan, jadi tidak boleh
disimpan di cache dan halaman tidak boleh disematkan di situs lain.
"""


def test_balasan_melarang_penebakan_tipe_isi(klien):
    balasan = klien.get("/api/auth/me")

    assert balasan.headers["X-Content-Type-Options"] == "nosniff"


def test_balasan_melarang_penyematan_di_situs_lain(klien):
    balasan = klien.get("/api/auth/me")

    assert balasan.headers["X-Frame-Options"] == "DENY"


def test_balasan_tidak_membocorkan_alamat_asal(klien):
    balasan = klien.get("/api/auth/me")

    assert balasan.headers["Referrer-Policy"] == "no-referrer"


def test_kebijakan_keamanan_konten_terpasang(klien):
    kebijakan = klien.get("/api/auth/me").headers["Content-Security-Policy"]

    assert "default-src 'self'" in kebijakan
    assert "frame-ancestors 'none'" in kebijakan
    assert "object-src 'none'" in kebijakan


def test_kebijakan_mengizinkan_google_fonts_saja_sebagai_pihak_luar(klien):
    kebijakan = klien.get("/api/auth/me").headers["Content-Security-Policy"]

    assert "https://fonts.googleapis.com" in kebijakan
    assert "https://fonts.gstatic.com" in kebijakan


def test_data_pribadi_tidak_boleh_disimpan_cache(klien_masuk):
    """Rekap memuat data yang bersumber dari identitas pemilik kendaraan."""
    balasan = klien_masuk.get("/api/rekap")

    assert balasan.status_code == 200
    assert balasan.headers["Cache-Control"] == "no-store"


def test_balasan_401_juga_membawa_header_keamanan(klien):
    balasan = klien.get("/api/rekap")

    assert balasan.status_code == 401
    assert balasan.headers["X-Frame-Options"] == "DENY"
