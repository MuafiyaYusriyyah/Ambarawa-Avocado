"""Koneksi MySQL, pembuatan tabel otomatis, dan data awal daftar akun."""
import datetime as dt
from contextlib import contextmanager

import mysql.connector

from config import DB


def _connect(dengan_db=True):
    cfg = dict(DB)
    if not dengan_db:
        cfg.pop("database")
    return mysql.connector.connect(charset="utf8mb4", **cfg)


@contextmanager
def cursor(commit=False):
    """with cursor(commit=True) as c: c.execute(...)  -> baris berupa dict."""
    conn = _connect()
    cur = conn.cursor(dictionary=True)
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


SKEMA = [
    """CREATE TABLE IF NOT EXISTS akun (
        kode VARCHAR(10) PRIMARY KEY,
        nama VARCHAR(100) NOT NULL,
        kelompok VARCHAR(20) NOT NULL,
        saldo_normal CHAR(1) NOT NULL,
        sistem TINYINT NOT NULL DEFAULT 0
    ) ENGINE=InnoDB""",
    """CREATE TABLE IF NOT EXISTS pengaturan (
        id INT PRIMARY KEY,
        nama_usaha VARCHAR(100),
        nama_periode VARCHAR(60),
        tgl_awal DATE,
        tgl_akhir DATE
    ) ENGINE=InnoDB""",
    """CREATE TABLE IF NOT EXISTS saldo_awal (
        kode VARCHAR(10) PRIMARY KEY,
        debit DECIMAL(18,2) NOT NULL DEFAULT 0,
        kredit DECIMAL(18,2) NOT NULL DEFAULT 0,
        qty DECIMAL(18,2) NOT NULL DEFAULT 0,
        FOREIGN KEY (kode) REFERENCES akun(kode)
    ) ENGINE=InnoDB""",
    """CREATE TABLE IF NOT EXISTS jurnal (
        id INT AUTO_INCREMENT PRIMARY KEY,
        tanggal DATE NOT NULL,
        bukti VARCHAR(30),
        keterangan VARCHAR(255),
        jenis VARCHAR(4) NOT NULL,           -- JU = umum, AJP = penyesuaian, PNT = penutup
        sumber VARCHAR(12) NOT NULL DEFAULT 'MANUAL',
        dibuat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB""",
    """CREATE TABLE IF NOT EXISTS jurnal_detail (
        id INT AUTO_INCREMENT PRIMARY KEY,
        jurnal_id INT NOT NULL,
        kode VARCHAR(10) NOT NULL,
        debit DECIMAL(18,2) NOT NULL DEFAULT 0,
        kredit DECIMAL(18,2) NOT NULL DEFAULT 0,
        FOREIGN KEY (jurnal_id) REFERENCES jurnal(id) ON DELETE CASCADE,
        FOREIGN KEY (kode) REFERENCES akun(kode)
    ) ENGINE=InnoDB""",
    """CREATE TABLE IF NOT EXISTS persediaan_mutasi (
        id INT AUTO_INCREMENT PRIMARY KEY,
        tanggal DATE NOT NULL,
        kode VARCHAR(10) NOT NULL,           -- akun persediaan (1-104 / 1-105)
        jenis VARCHAR(6) NOT NULL,           -- MASUK / KELUAR
        qty DECIMAL(18,2) NOT NULL,
        harga DECIMAL(18,4) NOT NULL,        -- harga per kg (beli atau HPP rata-rata)
        total DECIMAL(18,2) NOT NULL,
        keterangan VARCHAR(255),
        jurnal_id INT,
        FOREIGN KEY (kode) REFERENCES akun(kode)
    ) ENGINE=InnoDB""",
]

# (kode, nama, kelompok, saldo normal)
AKUN = [
    ("1-101", "Kas", "Aset", "D"),
    ("1-102", "Bank BRI", "Aset", "D"),
    ("1-103", "Piutang Usaha", "Aset", "D"),
    ("1-104", "Persediaan Alpukat Segar", "Aset", "D"),
    ("1-105", "Persediaan Alpukat Frozen", "Aset", "D"),
    ("1-106", "Peralatan Usaha", "Aset", "D"),
    ("1-107", "Peralatan Pengolahan Frozen", "Aset", "D"),
    ("1-108", "Akumulasi Penyusutan Peralatan", "Aset", "K"),
    ("2-101", "Utang Usaha", "Liabilitas", "K"),
    ("2-102", "Utang Gaji", "Liabilitas", "K"),
    ("3-101", "Modal Pemilik", "Ekuitas", "K"),
    ("3-102", "Prive", "Ekuitas", "D"),
    ("3-103", "Ikhtisar Laba Rugi", "Ekuitas", "K"),
    ("4-101", "Penjualan Alpukat Segar", "Pendapatan", "K"),
    ("4-102", "Penjualan Alpukat Frozen", "Pendapatan", "K"),
    ("4-103", "Penjualan Alpukat untuk Jus", "Pendapatan", "K"),
    ("4-104", "Pendapatan Lain-lain", "Pendapatan", "K"),
    ("4-105", "Retur Penjualan", "Pendapatan", "D"),
    ("4-106", "Potongan Penjualan", "Pendapatan", "D"),
    ("5-101", "Pembelian Alpukat Segar", "Pembelian", "D"),
    ("5-102", "Retur Pembelian", "Pembelian", "K"),
    ("5-103", "Potongan Pembelian", "Pembelian", "K"),
    ("6-101", "HPP Alpukat Segar", "HPP", "D"),
    ("6-102", "HPP Alpukat Frozen", "HPP", "D"),
    ("6-103", "HPP Alpukat untuk Jus", "HPP", "D"),
    ("7-101", "Beban Gaji", "Beban", "D"),
    ("7-102", "Beban Perawatan Tanaman", "Beban", "D"),
    ("7-103", "Beban Produksi Frozen", "Beban", "D"),
    ("7-104", "Beban Pengiriman", "Beban", "D"),
    ("7-105", "Beban Penyusutan", "Beban", "D"),
    ("7-106", "Beban Perlengkapan", "Beban", "D"),
    ("7-107", "Beban Kompensasi Kerusakan Barang", "Beban", "D"),
    ("7-108", "Beban Operasional Lainnya", "Beban", "D"),
]


def siapkan_database():
    """Buat database + tabel bila belum ada, lalu isi daftar akun pertama kali."""
    conn = _connect(dengan_db=False)
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB['database']}` CHARACTER SET utf8mb4")
    conn.commit()
    cur.close()
    conn.close()

    with cursor(commit=True) as c:
        for sql in SKEMA:
            c.execute(sql)
        c.execute("SELECT COUNT(*) n FROM akun")
        if c.fetchone()["n"] == 0:
            for kode, nama, kel, normal in AKUN:
                sistem = 1 if kode == "3-103" else 0
                c.execute(
                    "INSERT INTO akun (kode,nama,kelompok,saldo_normal,sistem) VALUES (%s,%s,%s,%s,%s)",
                    (kode, nama, kel, normal, sistem),
                )
        c.execute("SELECT COUNT(*) n FROM pengaturan")
        if c.fetchone()["n"] == 0:
            th = dt.date.today().year
            c.execute(
                "INSERT INTO pengaturan (id,nama_usaha,nama_periode,tgl_awal,tgl_akhir) VALUES (1,%s,%s,%s,%s)",
                ("Ambarawa Avocado", f"Periode {th}", dt.date(th, 1, 1), dt.date(th, 12, 31)),
            )
