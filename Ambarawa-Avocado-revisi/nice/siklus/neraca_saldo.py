"""TAHAP 3 - NERACA SALDO (sebelum penyesuaian).
Saldo akhir tiap akun dari saldo awal + jurnal umum. Total debit harus sama dengan total kredit."""
import streamlit as st

from core.buku import Buku
from core.util import B, Z, kol, rp, sisi
from ui.komponen import tampil

KOL_SALDO = kol(("Kode", 90, "w"), ("Nama Akun", 420, "w"), ("Debit", 180, "e"), ("Kredit", 180, "e"))


def susun(b, net):
    """Susun tabel neraca saldo dari saldo bersih tiap akun {kode: debit - kredit}. Dipakai juga oleh neraca_saldo_akhir.py."""
    rows, td, tk = [], Z, Z
    for a in b.akun:
        d, k = sisi(net[a["kode"]])
        if d or k:
            rows.append(B(a["kode"], a["nama"], d, k))
            td, tk = td + d, tk + k
    return KOL_SALDO, rows + [B("", "TOTAL", td, tk, tag="b")]


def tabel(b):
    return susun(b, b.net(("JU",)))


def halaman():
    kolom, rows = tabel(Buku())
    td, tk = rows[-1][0][2], rows[-1][0][3]
    if td or tk:
        if td == tk:
            st.success("Neraca saldo seimbang.")
        else:
            st.warning(f"Belum seimbang, selisih Rp {rp(abs(td - tk))}.")
    tampil(kolom, rows)
