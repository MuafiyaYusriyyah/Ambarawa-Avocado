"""Koneksi MySQL, pembuatan tabel otomatis, daftar akun awal, dan migrasi dari versi lama."""
import datetime as dt
from contextlib import contextmanager

import mysql.connector

from core.config import DB
from core.konstanta import DIKUNCI


def konek(pakai_db=True):
    cfg = dict(DB)
    if not pakai_db:
        cfg.pop("database")
    return mysql.connector.connect(charset="utf8mb4", **cfg)


@contextmanager
def cursor(commit=False):
    """with cursor(True) as c: c.execute(...)  -> baris hasil berupa dict."""
    conn = konek()
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


def ambil(sql, *param):
    with cursor() as c:
        c.execute(sql, param)
        return c.fetchall()


SKEMA = [
    "CREATE TABLE IF NOT EXISTS akun (kode VARCHAR(10) PRIMARY KEY, nama VARCHAR(100), kelompok VARCHAR(20), "
    "saldo_normal CHAR(1), sistem TINYINT DEFAULT 0)",
    "CREATE TABLE IF NOT EXISTS pengaturan (id INT PRIMARY KEY, nama_usaha VARCHAR(100), nama_periode VARCHAR(60), "
    "tgl_awal DATE, tgl_akhir DATE)",
    "CREATE TABLE IF NOT EXISTS saldo_awal (kode VARCHAR(10) PRIMARY KEY, debit DECIMAL(18,2) DEFAULT 0, "
    "kredit DECIMAL(18,2) DEFAULT 0, qty DECIMAL(18,2) DEFAULT 0)",
    "CREATE TABLE IF NOT EXISTS jurnal (id INT AUTO_INCREMENT PRIMARY KEY, tanggal DATE, bukti VARCHAR(30), "
    "keterangan VARCHAR(255), jenis VARCHAR(4), sumber VARCHAR(12) DEFAULT 'MANUAL')",   # jenis: JU, AJP, PNT
    "CREATE TABLE IF NOT EXISTS jurnal_detail (id INT AUTO_INCREMENT PRIMARY KEY, jurnal_id INT, kode VARCHAR(10), "
    "debit DECIMAL(18,2) DEFAULT 0, kredit DECIMAL(18,2) DEFAULT 0, "
    "FOREIGN KEY (jurnal_id) REFERENCES jurnal(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS persediaan_mutasi (id INT AUTO_INCREMENT PRIMARY KEY, tanggal DATE, kode VARCHAR(10), "
    "jenis VARCHAR(6), qty DECIMAL(18,2), harga DECIMAL(18,4), total DECIMAL(18,2), keterangan VARCHAR(255), jurnal_id INT)",
    # semua input Penerimaan / Pengeluaran / Transaksi Lainnya dicatat di sini, lalu otomatis menjadi jurnal umum
    "CREATE TABLE IF NOT EXISTS transaksi (id INT AUTO_INCREMENT PRIMARY KEY, kelompok VARCHAR(8), item VARCHAR(80), "
    "no_bukti VARCHAR(30), tanggal DATE, pihak VARCHAR(100), jenis VARCHAR(40), qty DECIMAL(18,2), harga DECIMAL(18,2), "
    "total DECIMAL(18,2), cara VARCHAR(30), keterangan VARCHAR(255), jurnal_id INT)",
    "CREATE TABLE IF NOT EXISTS migrasi (nama VARCHAR(40) PRIMARY KEY)",
]

# kode | nama | kelompok | saldo normal (D/K)
AKUN = """1-101|Kas|Aset|D
1-102|Bank BRI|Aset|D
1-103|Piutang Usaha|Aset|D
1-104|Persediaan Alpukat Segar|Aset|D
1-105|Persediaan Alpukat Frozen|Aset|D
1-106|Peralatan Usaha|Aset|D
1-107|Peralatan Pengolahan Frozen|Aset|D
1-108|Akumulasi Penyusutan Peralatan|Aset|K
2-101|Utang Usaha|Liabilitas|K
2-102|Utang Gaji|Liabilitas|K
3-101|Modal Pemilik|Ekuitas|K
3-102|Prive|Ekuitas|D
3-103|Ikhtisar Laba Rugi|Ekuitas|K
4-101|Penjualan Alpukat Segar|Pendapatan|K
4-102|Penjualan Alpukat Frozen|Pendapatan|K
4-103|Penjualan Alpukat untuk Jus|Pendapatan|K
4-104|Pendapatan Lain-lain|Pendapatan|K
4-105|Retur Penjualan|Pendapatan|D
4-106|Potongan Penjualan|Pendapatan|D
5-101|Pembelian Alpukat Segar|Pembelian|D
5-102|Retur Pembelian|Pembelian|K
5-103|Potongan Pembelian|Pembelian|K
6-101|HPP Alpukat Segar|HPP|D
6-102|HPP Alpukat Frozen|HPP|D
6-103|HPP Alpukat untuk Jus|HPP|D
7-101|Beban Gaji|Beban|D
7-102|Beban Perawatan Tanaman|Beban|D
7-103|Beban Produksi Frozen|Beban|D
7-104|Beban Pengiriman|Beban|D
7-105|Beban Penyusutan|Beban|D
7-106|Beban Perlengkapan|Beban|D
7-107|Beban Kompensasi Kerusakan Barang|Beban|D
7-108|Beban Operasional Lainnya|Beban|D
7-109|Beban Air|Beban|D
7-110|Beban Listrik|Beban|D"""


def _migrasi():
    """Penyesuaian satu kali untuk database dari versi lama. Dicatat di tabel `migrasi` supaya tidak diulang
    (jadi akun yang sudah dihapus pengguna tidak muncul lagi)."""
    sudah = {r["nama"] for r in ambil("SELECT nama FROM migrasi")}
    nota_lama = []
    if "nota_ke_transaksi" not in sudah:
        try:
            nota_lama = ambil("SELECT * FROM nota ORDER BY id")
        except Exception:
            nota_lama = []                      # tabel nota tidak ada = instalasi baru
    with cursor(True) as c:
        if "akun_air_listrik" not in sudah:
            for kode, nama in (("7-109", "Beban Air"), ("7-110", "Beban Listrik")):
                c.execute("SELECT kode FROM akun WHERE kode=%s", (kode,))
                if not c.fetchall():
                    c.execute("INSERT INTO akun (kode,nama,kelompok,saldo_normal,sistem) VALUES (%s,%s,'Beban','D',0)", (kode, nama))
            c.execute("INSERT INTO migrasi (nama) VALUES ('akun_air_listrik')")
        if "nota_ke_transaksi" not in sudah:
            for n in nota_lama:
                jual = n["tipe"] == "JUAL"
                c.execute("INSERT INTO transaksi (kelompok,item,no_bukti,tanggal,pihak,jenis,qty,harga,total,cara,keterangan,jurnal_id) "
                          "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'',%s)",
                          ("TERIMA" if jual else "KELUAR", ("Penjualan " if jual else "Pembelian ") + str(n["jenis"]), n["no_nota"],
                           n["tanggal"], n["pihak"], n["jenis"], n["qty"], n["harga"], n["total"], n["cara"], n["jurnal_id"]))
            c.execute("INSERT INTO migrasi (nama) VALUES ('nota_ke_transaksi')")


def siapkan_database():
    """Buat database + tabel bila belum ada, lalu isi daftar akun dan periode pertama kali."""
    try:                                    # di hosting, database biasanya sudah disediakan dan user tidak boleh membuatnya
        conn = konek(False)
        conn.cursor().execute(f"CREATE DATABASE IF NOT EXISTS `{DB['database']}` CHARACTER SET utf8mb4")
        conn.commit()
        conn.close()
    except Exception:
        pass
    with cursor(True) as c:
        for sql in SKEMA:
            c.execute(sql)
        c.execute("SELECT COUNT(*) n FROM akun")
        if c.fetchone()["n"] == 0:
            for baris in AKUN.splitlines():
                kode, nama, kel, normal = baris.split("|")
                c.execute("INSERT INTO akun (kode,nama,kelompok,saldo_normal,sistem) VALUES (%s,%s,%s,%s,%s)",
                          (kode, nama, kel, normal, 1 if kode in DIKUNCI else 0))
        c.execute("SELECT COUNT(*) n FROM pengaturan")
        if c.fetchone()["n"] == 0:
            th = dt.date.today().year
            c.execute("INSERT INTO pengaturan VALUES (1,%s,%s,%s,%s)",
                      ("Ambarawa Avocado", f"Periode {th}", dt.date(th, 1, 1), dt.date(th, 12, 31)))
    _migrasi()
