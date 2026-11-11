"""Sistem persediaan perpetual, metode rata-rata bergerak (moving average).
Setiap transaksi persediaan otomatis membuat jurnal umum (sumber = PERSEDIAAN),
sehingga langsung ikut ke buku besar sampai neraca saldo akhir.
"""
from decimal import Decimal as D, ROUND_HALF_UP

from db import cursor

Z = D("0")
SEN = D("0.01")

STOK = {"1-104": "Alpukat Segar", "1-105": "Alpukat Frozen"}
PRODUK = {   # produk jual -> akun persediaan, pendapatan, HPP
    "segar": dict(nama="Alpukat Segar", persediaan="1-104", pendapatan="4-101", hpp="6-101"),
    "frozen": dict(nama="Alpukat Frozen", persediaan="1-105", pendapatan="4-102", hpp="6-102"),
    "jus": dict(nama="Alpukat untuk Penjual Jus (stok segar)", persediaan="1-104", pendapatan="4-103", hpp="6-103"),
}
PEMBAYARAN = {"1-101": "Tunai (Kas)", "1-102": "Transfer (Bank BRI)", "2-101": "Belum dibayar (Utang Usaha)"}
PENERIMAAN = {"1-101": "Tunai (Kas)", "1-102": "Transfer (Bank BRI)", "1-103": "Kredit (Piutang Usaha)"}


def dec(v):
    return D(str(v)) if v not in (None, "") else Z


def r2(x):
    return x.quantize(SEN, rounding=ROUND_HALF_UP)


def _keadaan(cur, kode):
    cur.execute("SELECT debit,kredit,qty FROM saldo_awal WHERE kode=%s", (kode,))
    r = cur.fetchone()
    qty = dec(r["qty"]) if r else Z
    nilai = dec(r["debit"]) - dec(r["kredit"]) if r else Z
    cur.execute("SELECT jenis,qty,total FROM persediaan_mutasi WHERE kode=%s ORDER BY id", (kode,))
    for m in cur.fetchall():
        s = 1 if m["jenis"] == "MASUK" else -1
        qty += s * dec(m["qty"])
        nilai += s * dec(m["total"])
    return qty, nilai


def _jurnal(cur, tanggal, ket, baris, prefix="PSD"):
    cur.execute("INSERT INTO jurnal (tanggal,bukti,keterangan,jenis,sumber) VALUES (%s,'',%s,'JU','PERSEDIAAN')",
                (tanggal, ket))
    jid = cur.lastrowid
    cur.execute("UPDATE jurnal SET bukti=%s WHERE id=%s", (f"{prefix}-{jid:04d}", jid))
    for kode, d, k in baris:
        cur.execute("INSERT INTO jurnal_detail (jurnal_id,kode,debit,kredit) VALUES (%s,%s,%s,%s)", (jid, kode, d, k))
    return jid


def _mutasi(cur, tanggal, kode, jenis, qty, harga, total, ket, jid):
    cur.execute(
        "INSERT INTO persediaan_mutasi (tanggal,kode,jenis,qty,harga,total,keterangan,jurnal_id) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (tanggal, kode, jenis, qty, harga, total, ket, jid))


def pembelian(tanggal, qty, harga, bayar, ket):
    if qty <= 0 or harga <= 0:
        raise ValueError("Jumlah (kg) dan harga per kg harus lebih dari 0.")
    if bayar not in PEMBAYARAN:
        raise ValueError("Cara pembayaran tidak dikenal.")
    total = r2(qty * harga)
    with cursor(commit=True) as c:
        ket2 = f"Pembelian alpukat segar {qty} kg" + (f" - {ket}" if ket else "")
        jid = _jurnal(c, tanggal, ket2, [("1-104", total, Z), (bayar, Z, total)])
        _mutasi(c, tanggal, "1-104", "MASUK", qty, harga, total, ket, jid)


def penjualan(tanggal, produk, qty, harga_jual, terima, ket):
    p = PRODUK.get(produk)
    if not p:
        raise ValueError("Produk tidak dikenal.")
    if qty <= 0 or harga_jual <= 0:
        raise ValueError("Jumlah (kg) dan harga jual per kg harus lebih dari 0.")
    if terima not in PENERIMAAN:
        raise ValueError("Cara penerimaan tidak dikenal.")
    with cursor(commit=True) as c:
        stok, nilai = _keadaan(c, p["persediaan"])
        if qty > stok:
            raise ValueError(f"Stok {STOK[p['persediaan']]} tidak cukup (tersedia {stok} kg).")
        hpp = nilai if qty == stok else r2(nilai * qty / stok)
        omzet = r2(qty * harga_jual)
        ket2 = f"Penjualan {p['nama'].lower()} {qty} kg" + (f" - {ket}" if ket else "")
        jid = _jurnal(c, tanggal, ket2, [
            (terima, omzet, Z), (p["pendapatan"], Z, omzet),
            (p["hpp"], hpp, Z), (p["persediaan"], Z, hpp)], prefix="PJL")
        _mutasi(c, tanggal, p["persediaan"], "KELUAR", qty, hpp / qty, hpp, ket, jid)


def produksi_frozen(tanggal, qty_segar, qty_frozen, ket):
    if qty_segar <= 0 or qty_frozen <= 0:
        raise ValueError("Jumlah segar yang diolah dan hasil frozen harus lebih dari 0.")
    with cursor(commit=True) as c:
        stok, nilai = _keadaan(c, "1-104")
        if qty_segar > stok:
            raise ValueError(f"Stok alpukat segar tidak cukup (tersedia {stok} kg).")
        biaya = nilai if qty_segar == stok else r2(nilai * qty_segar / stok)
        ket2 = f"Produksi frozen: {qty_segar} kg segar -> {qty_frozen} kg frozen" + (f" - {ket}" if ket else "")
        jid = _jurnal(c, tanggal, ket2, [("1-105", biaya, Z), ("1-104", Z, biaya)], prefix="PRD")
        _mutasi(c, tanggal, "1-104", "KELUAR", qty_segar, biaya / qty_segar, biaya, ket, jid)
        _mutasi(c, tanggal, "1-105", "MASUK", qty_frozen, biaya / qty_frozen, biaya, ket, jid)


def hapus(jurnal_id):
    """Hanya boleh menghapus transaksi paling akhir pada tiap stok (agar HPP rata-rata tetap konsisten)."""
    with cursor(commit=True) as c:
        c.execute("SELECT id,kode FROM persediaan_mutasi WHERE jurnal_id=%s", (jurnal_id,))
        grup = c.fetchall()
        if not grup:
            raise ValueError("Transaksi persediaan tidak ditemukan.")
        for g in grup:
            c.execute("SELECT COUNT(*) n FROM persediaan_mutasi WHERE kode=%s AND id>%s", (g["kode"], g["id"]))
            if c.fetchone()["n"]:
                raise ValueError("Hapus dulu transaksi persediaan yang lebih baru; hanya transaksi terakhir yang bisa dihapus.")
        c.execute("DELETE FROM persediaan_mutasi WHERE jurnal_id=%s", (jurnal_id,))
        c.execute("DELETE FROM jurnal WHERE id=%s", (jurnal_id,))


def kartu_stok(kode):
    """Kartu stok satu persediaan: baris-baris mutasi dengan saldo qty, nilai, dan harga rata-rata."""
    with cursor() as c:
        c.execute("SELECT debit,kredit,qty FROM saldo_awal WHERE kode=%s", (kode,))
        sa = c.fetchone()
        c.execute("SELECT * FROM persediaan_mutasi WHERE kode=%s ORDER BY id", (kode,))
        mut = c.fetchall()
    qty = dec(sa["qty"]) if sa else Z
    nilai = (dec(sa["debit"]) - dec(sa["kredit"])) if sa else Z
    rows = []
    if qty or nilai:
        rows.append(dict(tgl=None, ket="Persediaan awal", jenis="AWAL", qty=qty, harga=(nilai / qty if qty else Z),
                         total=nilai, sq=qty, sn=nilai, jid=None, terakhir=False))
    for m in mut:
        s = 1 if m["jenis"] == "MASUK" else -1
        qty += s * dec(m["qty"])
        nilai += s * dec(m["total"])
        rows.append(dict(tgl=m["tanggal"], ket=m["keterangan"], jenis=m["jenis"], qty=dec(m["qty"]),
                         harga=dec(m["harga"]), total=dec(m["total"]), sq=qty, sn=nilai, jid=m["jurnal_id"], terakhir=False))
    if rows:
        rows[-1]["terakhir"] = True
    return dict(kode=kode, nama=STOK[kode], rows=rows, qty=qty, nilai=nilai, rata=(nilai / qty if qty else Z))
