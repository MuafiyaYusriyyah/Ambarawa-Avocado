"""TAHAP 2 - BUKU BESAR (sebelum penyesuaian).
Semua akun ditampilkan dalam satu tabel: saldo awal + mutasi dari jurnal umum, lengkap dengan saldo berjalan."""
from collections import defaultdict

from core.buku import Buku
from core.util import B, Z, kol
from ui.komponen import tampil

KOL_BB = kol(("Tanggal", 105, "w"), ("Keterangan", 430, "w"), ("Bukti", 90, "w"), ("Debit", 140, "e"), ("Kredit", 140, "e"), ("Saldo", 160, "e"))


def buku_besar(b, jenis=("JU",)):
    """Buku besar dari jurnal berjenis `jenis`. Dipakai juga oleh bukbes_ajp.py (JU + AJP)."""
    per = defaultdict(list)
    for l in b.baris:
        if l["jenis"] in jenis:
            per[l["kode"]].append((l["tanggal"], l["keterangan"], l["bukti"], l["debit"], l["kredit"], l["jenis"]))
    rows = []
    for a in b.akun:
        d0, k0, _ = b.sa.get(a["kode"], (Z, Z, Z))
        isi = ([(None, "Saldo awal", "SA", d0, k0, "SA")] if d0 or k0 else []) + per[a["kode"]]
        if not isi:
            continue
        rows.append(B("", f"{a['kode']}   {a['nama']}", tag="b"))
        s, td, tk = Z, Z, Z
        for tg, ket, bk, d, k, jn in isi:
            s += (d - k) * (1 if a["saldo_normal"] == "D" else -1)
            td, tk = td + d, tk + k
            rows.append(B(tg, (ket or "") + ("   [penyesuaian]" if jn == "AJP" else ""), bk, d, k, s))
        rows.append(B("", f"Jumlah {a['nama']}", "", td, tk, s, tag="b"))
    return KOL_BB, rows or [B("", "Belum ada data.", tag="kosong")]


def tabel(b):
    return buku_besar(b, ("JU",))


def halaman():
    tampil(*tabel(Buku()))
