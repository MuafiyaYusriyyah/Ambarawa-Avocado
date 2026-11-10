"""Pengaturan koneksi MySQL.
Ubah nilai default di bawah ini, atau set environment variable (DB_USER, DB_PASSWORD, dst).
"""
import os

DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),       # kosong = tanpa password
    "database": os.getenv("DB_NAME", "alpukat estate"),
}

SECRET_KEY = os.getenv("SECRET_KEY", "kebun-alpukat-ambarawa")
