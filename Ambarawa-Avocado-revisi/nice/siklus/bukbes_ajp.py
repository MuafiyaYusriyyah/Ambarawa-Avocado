"""TAHAP 5 - BUKU BESAR SETELAH PENYESUAIAN.
Sama dengan buku besar tahap 2, tetapi jurnal penyesuaian (AJP) ikut dimasukkan."""
from core.buku import Buku
from siklus.bukbes import buku_besar
from ui.komponen import tampil


def tabel(b):
    return buku_besar(b, ("JU", "AJP"))


def halaman():
    tampil(*tabel(Buku()))
