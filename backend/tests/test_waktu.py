"""Tes untuk app/waktu.py — sumber tunggal tanggal "hari ini".

Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 2 (aturan kode) dan 7.2.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.utils.waktu import ZONA, hari_ini


def test_memakai_app_today_bila_diisi(monkeypatch):
    monkeypatch.setenv("APP_TODAY", "2026-09-19")
    assert hari_ini() == date(2026, 9, 19)


def test_app_today_kosong_dianggap_tidak_diset(monkeypatch):
    monkeypatch.setenv("APP_TODAY", "   ")
    assert hari_ini() == datetime.now(ZONA).date()


def test_tanpa_app_today_memakai_tanggal_zona_jakarta(monkeypatch):
    monkeypatch.delenv("APP_TODAY", raising=False)
    assert hari_ini() == datetime.now(ZoneInfo("Asia/Jakarta")).date()


def test_app_today_format_salah_menimbulkan_error(monkeypatch):
    monkeypatch.setenv("APP_TODAY", "19/09/2026")
    with pytest.raises(ValueError, match="APP_TODAY"):
        hari_ini()


def test_app_today_tanggal_mustahil_menimbulkan_error(monkeypatch):
    monkeypatch.setenv("APP_TODAY", "2026-02-31")
    with pytest.raises(ValueError, match="APP_TODAY"):
        hari_ini()
