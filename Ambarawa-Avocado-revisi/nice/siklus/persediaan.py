"""PERSEDIAAN (kartu stok) - metode perpetual dengan harga rata-rata bergerak.
Setiap pembelian / penjualan / produksi yang melibatkan alpukat (kg) mencatat mutasi di sini,
sehingga nilai stok di neraca dan harga pokok penjualan (HPP) selalu sejalan dengan jurnal umum."""
from decimal import Decimal as D, ROUND_HALF_UP

import streamlit as st

from core.buku import Buku
from core.db import ambil, cursor
from core.konstanta import STOK
from core.util import B, Z, dec, kol
from ui.komponen import tampil

# produk yang bisa dijual: nama, akun stok, akun penjualan, akun HPP
PRODUK = {"segar": dict(nama="Alpukat Segar", stok="1-104", jual="4-101", hpp="6-101"),
          "frozen": dict(nama="Alpukat Frozen", stok="1-105", jual="4-102", hpp="6-102"),
          "jus": dict(nama="Alpukat untuk Penjual Jus", stok="1-104", jual="4-103", hpp="6-103")}
# produk yang bisa dibeli
BELI = {"segar": dict(nama="Alpukat Segar", stok="1-104"), "frozen": dict(nama="Alpukat Frozen", stok="1-105")}

KOL_KARTU = kol(("Tanggal", 100, "w"), ("Keterangan", 300, "w"), ("Mutasi", 70, "w"), ("Jumlah kg", 90, "e"), ("Harga/kg", 100, "e"),
                ("Nilai (Rp)", 120, "e"), ("Saldo kg", 90, "e"), ("Saldo Rp", 130, "e"))


def r2(x):
    return x.quantize(D("0.01"), ROUND_HALF_UP)


def kgs(q):
    return f"{q.normalize():f}"


def keadaan(c, kode):
    """(jumlah kg, nilai Rp) persediaan saat ini."""
    c.execute("SELECT debit,kredit,qty FROM saldo_awal WHERE kode=%s", (kode,))
    s = c.fetchone()
    q, n = (dec(s["qty"]), dec(s["debit"]) - dec(s["kredit"])) if s else (Z, Z)
    c.execute("SELECT jenis,qty,total FROM persediaan_mutasi WHERE kode=%s ORDER BY id", (kode,))
    for m in c.fetchall():
        t = 1 if m["jenis"] == "MASUK" else -1
        q, n = q + t * dec(m["qty"]), n + t * dec(m["total"])
    return q, n


def stok(kode):
    with cursor() as c:
        return keadaan(c, kode)


def catat_mutasi(c, tgl, ket, jurnal_id, mutasi):
    """mutasi: [(kode, 'MASUK' / 'KELUAR', qty, total)]. Dipanggil dalam transaksi database yang sama dengan jurnalnya."""
    for kode, jenis, qty, total in mutasi:
        c.execute("INSERT INTO persediaan_mutasi (tanggal,kode,jenis,qty,harga,total,keterangan,jurnal_id) "
                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (tgl, kode, jenis, qty, total / qty, total, ket, jurnal_id))


def pastikan_terakhir(jurnal_id):
    """Transaksi hanya boleh dihapus bila yang paling akhir pada tiap stok, supaya harga rata-rata transaksi sesudahnya tidak berubah."""
    for m in ambil("SELECT id,kode FROM persediaan_mutasi WHERE jurnal_id=%s", jurnal_id):
        if ambil("SELECT id FROM persediaan_mutasi WHERE kode=%s AND id>%s", m["kode"], m["id"]):
            raise ValueError("Hapus dulu transaksi alpukat yang lebih baru. Hanya transaksi stok terakhir yang bisa dihapus.")


def tabel_kartu(kode):
    """Kartu stok persediaan (rata-rata bergerak)."""
    s = ambil("SELECT debit,kredit,qty FROM saldo_awal WHERE kode=%s", kode)
    q, n = (dec(s[0]["qty"]), dec(s[0]["debit"]) - dec(s[0]["kredit"])) if s else (Z, Z)
    rows = [B(None, "Persediaan awal", "Awal", q, n / q if q else Z, n, q, n)] if q or n else []
    for m in ambil("SELECT * FROM persediaan_mutasi WHERE kode=%s ORDER BY id", kode):
        t = 1 if m["jenis"] == "MASUK" else -1
        q, n = q + t * dec(m["qty"]), n + t * dec(m["total"])
        rows.append(B(m["tanggal"], m["keterangan"], m["jenis"].capitalize(), dec(m["qty"]), dec(m["harga"]), dec(m["total"]), q, n))
    return KOL_KARTU, (rows or [B("", "Belum ada mutasi.", tag="kosong")]) + [B("", "Saldo kartu stok", "", None, None, None, q, n, tag="b")]


def tabel_segar(b):
    return tabel_kartu("1-104")


def tabel_frozen(b):
    return tabel_kartu("1-105")


def halaman():
    st.caption("Kartu stok bergerak otomatis dari transaksi pembelian, penjualan, dan produksi frozen. Untuk membatalkan, hapus transaksinya di halaman Penerimaan / Pengeluaran / Transaksi Lainnya.")
    ada = {a["kode"] for a in Buku().akun}
    for kode, nama in STOK.items():
        if kode in ada:
            st.subheader(f"Kartu stok {nama}")
            tampil(*tabel_kartu(kode))
