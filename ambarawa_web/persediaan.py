"""Nota penjualan dan pembelian + persediaan perpetual (harga rata-rata bergerak).
Setiap nota otomatis membuat jurnal umum, mutasi kartu stok, dan catatan nota, dalam satu transaksi database."""
from decimal import Decimal as D, ROUND_HALF_UP

from akuntansi import Z, dec
from db import ambil, cursor

PRODUK = {"segar": dict(nama="Alpukat Segar", stok="1-104", jual="4-101", hpp="6-101"),       # produk yang bisa dijual
          "frozen": dict(nama="Alpukat Frozen", stok="1-105", jual="4-102", hpp="6-102"),
          "jus": dict(nama="Alpukat untuk Penjual Jus", stok="1-104", jual="4-103", hpp="6-103")}
BELI = {"segar": dict(nama="Alpukat Segar", stok="1-104"), "frozen": dict(nama="Alpukat Frozen", stok="1-105")}   # produk yang bisa dibeli
BELI_AKUN = {"Tunai": "1-101", "Transfer Bank BRI": "1-102", "Kredit": "2-101"}     # kredit = Utang Usaha
JUAL_AKUN = {"Tunai": "1-101", "Transfer Bank BRI": "1-102", "Kredit": "1-103"}     # kredit = Piutang Usaha


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


def catat(c, tgl, ket, jurnal, mutasi, prefix, bukti=""):
    """Simpan jurnal umum otomatis + mutasi kartu stok. jurnal: [(kode, debit, kredit)], mutasi: [(kode, jenis, qty, total)].
    Mengembalikan (id jurnal, nomor bukti)."""
    bukti = bukti.strip()
    c.execute("INSERT INTO jurnal (tanggal,bukti,keterangan,jenis,sumber) VALUES (%s,%s,%s,'JU','PERSEDIAAN')", (tgl, bukti, ket))
    jid = c.lastrowid
    if not bukti:
        bukti = f"{prefix}-{jid:04d}"
        c.execute("UPDATE jurnal SET bukti=%s WHERE id=%s", (bukti, jid))
    for x in jurnal:
        c.execute("INSERT INTO jurnal_detail (jurnal_id,kode,debit,kredit) VALUES (%s,%s,%s,%s)", (jid, *x))
    for kode, jenis, qty, total in mutasi:
        c.execute("INSERT INTO persediaan_mutasi (tanggal,kode,jenis,qty,harga,total,keterangan,jurnal_id) "
                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (tgl, kode, jenis, qty, total / qty, total, ket, jid))
    return jid, bukti


def catat_nota(c, tipe, bukti, tgl, pihak, jenis, qty, harga, total, cara, jid):
    c.execute("INSERT INTO nota (tipe,no_nota,tanggal,pihak,jenis,qty,harga,total,cara,jurnal_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
              (tipe, bukti, tgl, pihak.strip(), jenis, qty, harga, total, cara, jid))


def cek(qty, harga, pihak, sebutan, cara, akun):
    if not pihak.strip():
        raise ValueError(f"Nama {sebutan} wajib diisi.")
    if qty <= 0 or harga <= 0:
        raise ValueError("Jumlah (kg) dan harga per kg harus lebih dari 0.")
    if cara not in akun:
        raise ValueError("Cara pembayaran tidak dikenal.")


def beli(tgl, jenis, qty, harga, cara, nota, pihak):
    """Pembelian: debit persediaan, kredit kas / bank / utang usaha."""
    cek(qty, harga, pihak, "supplier", cara, BELI_AKUN)
    p, t = BELI[jenis], r2(qty * harga)
    with cursor(True) as c:
        jid, bukti = catat(c, tgl, f"Pembelian {p['nama'].lower()} {kgs(qty)} kg dari {pihak.strip()}",
                           [(p["stok"], t, Z), (BELI_AKUN[cara], Z, t)], [(p["stok"], "MASUK", qty, t)], "PB", nota)
        catat_nota(c, "BELI", bukti, tgl, pihak, p["nama"], qty, harga, t, cara, jid)


def jual(tgl, produk, qty, harga, cara, nota, pihak):
    """Penjualan: debit kas / bank / piutang, kredit penjualan; debit HPP, kredit persediaan (rata-rata bergerak)."""
    cek(qty, harga, pihak, "customer", cara, JUAL_AKUN)
    p = PRODUK[produk]
    with cursor(True) as c:
        q, n = keadaan(c, p["stok"])
        if qty > q:
            raise ValueError(f"Stok {p['nama']} tidak cukup (tersedia {kgs(q)} kg).")
        hpp, omzet = (n if qty == q else r2(n * qty / q)), r2(qty * harga)
        jid, bukti = catat(c, tgl, f"Penjualan {p['nama'].lower()} {kgs(qty)} kg ke {pihak.strip()}",
                           [(JUAL_AKUN[cara], omzet, Z), (p["jual"], Z, omzet), (p["hpp"], hpp, Z), (p["stok"], Z, hpp)],
                           [(p["stok"], "KELUAR", qty, hpp)], "PJ", nota)
        catat_nota(c, "JUAL", bukti, tgl, pihak, p["nama"], qty, harga, omzet, cara, jid)


def olah(tgl, qty_segar, qty_frozen, ket):
    """Produksi frozen: pindahkan nilai stok segar ke stok frozen sebesar harga rata-rata."""
    if qty_segar <= 0 or qty_frozen <= 0:
        raise ValueError("Jumlah segar dan hasil frozen harus lebih dari 0.")
    with cursor(True) as c:
        q, n = keadaan(c, "1-104")
        if qty_segar > q:
            raise ValueError(f"Stok segar tidak cukup (tersedia {kgs(q)} kg).")
        biaya = n if qty_segar == q else r2(n * qty_segar / q)
        catat(c, tgl, f"Produksi frozen {kgs(qty_segar)} kg segar jadi {kgs(qty_frozen)} kg frozen {ket}".strip(),
              [("1-105", biaya, Z), ("1-104", Z, biaya)], [("1-104", "KELUAR", qty_segar, biaya), ("1-105", "MASUK", qty_frozen, biaya)], "PRD")


def hapus(jid):
    """Hapus transaksi persediaan beserta jurnal dan notanya. Hanya transaksi paling akhir pada tiap stok,
    agar harga rata-rata transaksi sesudahnya tidak berubah."""
    mutasi = ambil("SELECT id,kode FROM persediaan_mutasi WHERE jurnal_id=%s", jid)
    if not mutasi:
        raise ValueError("Transaksi tidak ditemukan.")
    for m in mutasi:
        if ambil("SELECT id FROM persediaan_mutasi WHERE kode=%s AND id>%s", m["kode"], m["id"]):
            raise ValueError("Hapus dulu transaksi yang lebih baru. Hanya transaksi terakhir yang bisa dihapus.")
    with cursor(True) as c:
        c.execute("DELETE FROM persediaan_mutasi WHERE jurnal_id=%s", (jid,))
        c.execute("DELETE FROM nota WHERE jurnal_id=%s", (jid,))
        c.execute("DELETE FROM jurnal WHERE id=%s", (jid,))
