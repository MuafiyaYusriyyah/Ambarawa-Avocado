"""TAHAP 7 - LAPORAN KEUANGAN: Laba Rugi, Perubahan Ekuitas, dan Posisi Keuangan (neraca).
hitung(b) menghitung semua angka sekali; tiga tabel di bawahnya hanya menyusun tampilannya."""
import streamlit as st

from core.buku import Buku
from core.konstanta import LAIN, MODAL, PRIVE
from core.util import B, I, Z, kol
from ui.komponen import tampil

KOL_LAP = kol(("Keterangan", 520, "w"), ("Rincian", 170, "e"), ("Jumlah", 170, "e"))


def hitung(b):
    """Semua angka laporan, dihitung dari saldo awal + jurnal umum + jurnal penyesuaian."""
    if b._lap:
        return b._lap
    net = b.net(("JU", "AJP"))
    nat = lambda k: net[k] if b.a[k]["saldo_normal"] == "D" else -net[k]

    def grup(f, mentah=False):
        return [(a["kode"], a["nama"], net[a["kode"]] if mentah else nat(a["kode"]), a["saldo_normal"])
                for a in b.akun if f(a) and net[a["kode"]]]
    kel = lambda g: (lambda a: a["kelompok"] == g)
    p = dict(pend=grup(lambda a: a["kelompok"] == "Pendapatan" and a["kode"] != LAIN and a["saldo_normal"] == "K"),
             poto=grup(lambda a: a["kelompok"] == "Pendapatan" and a["saldo_normal"] == "D"),
             lain=grup(lambda a: a["kode"] == LAIN), beli=grup(kel("Pembelian")), hpp=grup(kel("HPP")),
             beban=grup(kel("Beban")), liab=grup(kel("Liabilitas")),
             lancar=grup(lambda a: a["kelompok"] == "Aset" and a["kode"] < "1-106", True),
             tetap=grup(lambda a: a["kelompok"] == "Aset" and a["kode"] >= "1-106", True))
    jml = lambda xs: sum((x[2] for x in xs), Z)
    p["pen_bersih"] = jml(p["pend"]) - jml(p["poto"])
    p["total_hpp"] = sum((x[2] if x[3] == "D" else -x[2] for x in p["beli"]), Z) + jml(p["hpp"])
    p["kotor"] = p["pen_bersih"] - p["total_hpp"]
    p["total_beban"] = jml(p["beban"])
    p["usaha"] = p["kotor"] - p["total_beban"]
    p["laba"] = p["usaha"] + jml(p["lain"])
    d0, k0, _ = b.sa.get(MODAL, (Z, Z, Z))
    md, mk = b.mut(("JU", "AJP"))[MODAL]
    p["modal_awal"], p["tambah"], p["prive"] = k0 - d0, mk - md, nat(PRIVE)
    p["modal_akhir"] = p["modal_awal"] + p["tambah"] + p["laba"] - p["prive"]
    p["t_lancar"], p["t_tetap"], p["t_liab"] = jml(p["lancar"]), jml(p["tetap"]), jml(p["liab"])
    b._lap = p
    return p


def laba_rugi(b):
    p = hitung(b)
    r = [B("Pendapatan", tag="b")] + [B(I + n, j) for _, n, j, _ in p["pend"]] + [B(I + "(-) " + n, j) for _, n, j, _ in p["poto"]]
    r += [B("Penjualan Bersih", None, p["pen_bersih"], tag="b"), B("Harga Pokok Penjualan", tag="b")]
    r += [B(I + ("(-) " if m == "K" else "") + n, j) for _, n, j, m in p["beli"]] + [B(I + n, j) for _, n, j, _ in p["hpp"]]
    r += [B("Total Harga Pokok Penjualan", None, p["total_hpp"], tag="b"), B("LABA KOTOR", None, p["kotor"], tag="b"), B("Beban Operasional", tag="b")]
    r += [B(I + n, j) for _, n, j, _ in p["beban"]]
    r += [B("Total Beban Operasional", None, p["total_beban"], tag="b"), B("LABA USAHA", None, p["usaha"], tag="b")]
    r += [B(n, None, j) for _, n, j, _ in p["lain"]]
    return KOL_LAP, r + [B("LABA BERSIH" if p["laba"] >= 0 else "RUGI BERSIH", None, p["laba"], tag="b")]


def ekuitas(b):
    p = hitung(b)
    return KOL_LAP, [B("Modal Pemilik, awal periode", None, p["modal_awal"]), B(I + "Penambahan modal", None, p["tambah"]),
                     B(I + ("Laba" if p["laba"] >= 0 else "Rugi") + " bersih periode berjalan", None, p["laba"]),
                     B(I + "Prive", None, -p["prive"]), B("MODAL PEMILIK, AKHIR PERIODE", None, p["modal_akhir"], tag="b")]


def posisi(b):
    p = hitung(b)
    r = [B("ASET", tag="b"), B("Aset Lancar", tag="b")] + [B(I + n, j) for _, n, j, _ in p["lancar"]]
    r += [B("Total Aset Lancar", None, p["t_lancar"], tag="b"), B("Aset Tetap", tag="b")] + [B(I + n, j) for _, n, j, _ in p["tetap"]]
    r += [B("Total Aset Tetap", None, p["t_tetap"], tag="b"), B("TOTAL ASET", None, p["t_lancar"] + p["t_tetap"], tag="b"), B("LIABILITAS", tag="b")]
    r += [B(I + n, j) for _, n, j, _ in p["liab"]]
    return KOL_LAP, r + [B("Total Liabilitas", None, p["t_liab"], tag="b"), B("EKUITAS", tag="b"), B(I + "Modal Pemilik", p["modal_akhir"]),
                         B("TOTAL LIABILITAS + EKUITAS", None, p["t_liab"] + p["modal_akhir"], tag="b")]


def halaman():
    b = Buku()
    for t, fn in zip(st.tabs(["Laba Rugi", "Perubahan Ekuitas", "Posisi Keuangan"]), (laba_rugi, ekuitas, posisi)):
        with t:
            tampil(*fn(b))
