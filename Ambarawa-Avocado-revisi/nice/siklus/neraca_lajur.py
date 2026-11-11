"""TAHAP 6 - NERACA LAJUR (kertas kerja).
Satu tabel 10 kolom: neraca saldo, penyesuaian, disesuaikan, laba rugi, dan neraca."""
from core.buku import Buku
from core.konstanta import LR
from core.util import B, Z, kol, sisi
from ui.komponen import tampil

KOL_NL = kol(("Kode", 70, "w"), ("Nama Akun", 250, "w"), *[(n, 112, "e") for n in (
    "NS Debit", "NS Kredit", "Penyesuaian D", "Penyesuaian K", "Disesuaikan D", "Disesuaikan K", "Laba Rugi D", "Laba Rugi K", "Neraca D", "Neraca K")])


def tabel(b):
    ns, aj = b.net(("JU",)), b.mut(("AJP",))
    rows, tot = [], [Z] * 10
    for a in b.akun:
        k = a["kode"]
        n, (ad, kd) = ns[k], aj[k]
        na = n + ad - kd
        if not (n or ad or kd or na):
            continue
        c = [*sisi(n), ad, kd, *sisi(na)]
        c += [*c[4:6], Z, Z] if a["kelompok"] in LR else [Z, Z, *c[4:6]]      # ke kolom laba rugi atau neraca
        rows.append(B(k, a["nama"], *c))
        tot = [t + x for t, x in zip(tot, c)]
    laba = tot[7] - tot[6]                      # kredit laba rugi - debit laba rugi
    sel = [Z] * 10
    if laba >= 0:                               # laba: debit laba rugi dan kredit neraca
        sel[6] = sel[9] = laba
    else:                                       # rugi: kredit laba rugi dan debit neraca
        sel[7] = sel[8] = -laba
    rows += [B("", "JUMLAH", *tot, tag="b"), B("", "LABA BERSIH" if laba >= 0 else "RUGI BERSIH", *sel, tag="b"),
             B("", "JUMLAH SEIMBANG", *[t + s for t, s in zip(tot, sel)], tag="b")]
    return KOL_NL, rows


def halaman():
    tampil(*tabel(Buku()))
