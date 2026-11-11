"""TAHAP 9 - NERACA SALDO AKHIR (setelah penutupan).
Hanya akun riil (aset, liabilitas, modal) yang tersisa; modal sudah berisi laba dan dikurangi prive."""
from core.buku import Buku
from core.konstanta import IKHTISAR, LR, MODAL, PRIVE
from core.util import Z
from siklus import laporan
from siklus.neraca_saldo import susun
from ui.komponen import tampil


def net_akhir(b):
    n, ma = b.net(("JU", "AJP")), laporan.hitung(b)["modal_akhir"]
    for k, a in b.a.items():
        if a["kelompok"] in LR:
            n[k] = Z
    n[PRIVE] = n[IKHTISAR] = Z
    n[MODAL] = -ma
    return n


def tabel(b):
    return susun(b, net_akhir(b))


def halaman():
    tampil(*tabel(Buku()))
