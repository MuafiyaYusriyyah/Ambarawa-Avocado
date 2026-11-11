"""Pengaturan koneksi MySQL.
Urutan pembacaan: .streamlit/secrets.toml (bagian [mysql]) -> environment variable (DB_HOST, DB_USER, ...) -> nilai default.
"""
import os

try:
    import streamlit as st
    _s = dict(st.secrets["mysql"])
except Exception:
    _s = {}


def _ambil(kunci, default):
    return _s.get(kunci) or os.getenv("DB_" + kunci.upper(), default)


DB = {
    "host": _ambil("host", "localhost"),
    "port": int(_ambil("port", 3306)),
    "user": _ambil("user", "root"),
    "password": _ambil("password", ""),          # kosong = tanpa password
    "database": _ambil("database", "alpukat estate"),
}
