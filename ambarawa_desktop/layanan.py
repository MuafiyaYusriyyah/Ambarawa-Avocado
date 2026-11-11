"""Lapisan layanan: format angka/tanggal, validasi input, dan semua proses simpan ke MySQL.
Dipakai oleh antarmuka desktop (main.py)."""
import datetime as dt
from decimal import Decimal as D, InvalidOperation

import akuntansi as ak
import db

Z = D("0")


def dec_(v):
    return D(str(v)) if v not in (None, "") else Z


# ------------------------------------------------------------ format tampilan
def rp(v, nol="-"):
    v = D(str(v or 0))
    if v == 0:
        return nol
    s = f"{abs(v):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    if s.endswith(",00"):
        s = s[:-3]
    return f"({s})" if v < 0 else s


def kg(v):
    v = D(str(v or 0))
    s = f"{v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return s[:-3] if s.endswith(",00") else s


def tgl(v):
    if not v:
        return ""
    bulan = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    return f"{v.day:02d} {bulan[v.month - 1]} {v.year}"


def tgl_input(v=None):
    return (v or dt.date.today()).strftime("%d-%m-%Y")


def polos(v):
    """Angka untuk kolom isian: 5000000 atau 12.5 (tanpa pemisah ribuan)."""
    v = D(str(v or 0))
    if v == 0:
        return ""
    return str(int(v)) if v == v.to_integral() else f"{v:.2f}"


# ------------------------------------------------------------ baca input
def angka(s, uang=True):
    """'1.500.000' / '1500000' / '1500,50' -> Decimal. Untuk uang, titik dengan 3 digit di belakangnya = pemisah ribuan."""
    s = (s or "").strip().lower().replace("rp", "").replace(" ", "")
    if not s:
        return Z
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif uang and (s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[1]) == 3)):
        s = s.replace(".", "")
    try:
        return D(s)
    except InvalidOperation:
        raise ValueError(f"Angka tidak valid: {s}")


def tanggal(s):
    s = (s or "").strip()
    for f in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s, f).date()
        except ValueError:
            pass
    raise ValueError("Tanggal tidak valid. Tulis dengan format HH-BB-TTTT, contoh 31-12-2026.")


# ------------------------------------------------------------ pengaturan & akun
def pengaturan():
    with db.cursor() as c:
        c.execute("SELECT * FROM pengaturan WHERE id=1")
        return c.fetchone()


def simpan_pengaturan(nama_usaha, nama_periode, awal, akhir):
    a, b = tanggal(awal), tanggal(akhir)
    if b < a:
        raise ValueError("Tanggal akhir tidak boleh sebelum tanggal awal.")
    with db.cursor(commit=True) as c:
        c.execute("UPDATE pengaturan SET nama_usaha=%s,nama_periode=%s,tgl_awal=%s,tgl_akhir=%s WHERE id=1",
                  (nama_usaha.strip() or "Ambarawa Avocado", nama_periode.strip(), a, b))


def daftar_akun():
    with db.cursor() as c:
        c.execute("SELECT * FROM akun ORDER BY kode")
        return c.fetchall()


def tambah_akun(kode, nama, kelompok, normal):
    kode, nama = kode.strip(), nama.strip()
    if not kode or not nama:
        raise ValueError("Kode dan nama akun wajib diisi.")
    if any(a["kode"] == kode for a in daftar_akun()):
        raise ValueError("Kode akun sudah dipakai.")
    with db.cursor(commit=True) as c:
        c.execute("INSERT INTO akun (kode,nama,kelompok,saldo_normal) VALUES (%s,%s,%s,%s)",
                  (kode, nama, kelompok, normal))


# ------------------------------------------------------------ saldo awal
def akun_saldo_awal():
    with db.cursor() as c:
        c.execute("""SELECT a.*, s.debit, s.kredit, s.qty FROM akun a LEFT JOIN saldo_awal s ON s.kode=a.kode
                     WHERE a.kelompok IN ('Aset','Liabilitas') OR a.kode='3-101' ORDER BY a.kode""")
        return c.fetchall()


def simpan_saldo_awal(isian):
    """isian: {kode: (saldo_teks, qty_teks)} -> (total debit, total kredit)."""
    akun = akun_saldo_awal()
    nilai, td, tk = [], Z, Z
    for a in akun:            # validasi semua dulu, baru simpan
        s, q = isian.get(a["kode"], ("", ""))
        v, qty = angka(s), angka(q, uang=False)
        if v < 0 or qty < 0:
            raise ValueError(f"Nilai negatif pada akun {a['nama']} tidak diperbolehkan.")
        d, k = (v, Z) if a["saldo_normal"] == "D" else (Z, v)
        td, tk = td + d, tk + k
        nilai.append((a["kode"], d, k, qty))
    with db.cursor(commit=True) as c:
        for kode, d, k, qty in nilai:
            c.execute("""INSERT INTO saldo_awal (kode,debit,kredit,qty) VALUES (%s,%s,%s,%s)
                         ON DUPLICATE KEY UPDATE debit=VALUES(debit),kredit=VALUES(kredit),qty=VALUES(qty)""",
                      (kode, d, k, qty))
    return td, tk


# ------------------------------------------------------------ jurnal
def simpan_jurnal(jenis, prefix, tanggal_s, bukti, ket, baris):
    """baris: [(kode, debit_teks, kredit_teks)]"""
    tgl_ = tanggal(tanggal_s)
    bersih = []
    for kode, d, k in baris:
        d, k = angka(d), angka(k)
        if kode and (d or k):
            if d and k:
                raise ValueError("Satu baris hanya boleh diisi di debit atau kredit, tidak keduanya.")
            if d < 0 or k < 0:
                raise ValueError("Nominal tidak boleh negatif.")
            bersih.append((kode, d, k))
        elif (d or k) and not kode:
            raise ValueError("Ada baris yang sudah diisi nominal tetapi akunnya belum dipilih.")
    if len(bersih) < 2:
        raise ValueError("Jurnal minimal terdiri dari dua baris akun.")
    td, tk = sum((x[1] for x in bersih), Z), sum((x[2] for x in bersih), Z)
    if td != tk:
        raise ValueError(f"Jurnal belum seimbang: debit {rp(td)} ≠ kredit {rp(tk)}.")
    with db.cursor(commit=True) as c:
        c.execute("INSERT INTO jurnal (tanggal,bukti,keterangan,jenis,sumber) VALUES (%s,%s,%s,%s,'MANUAL')",
                  (tgl_, bukti.strip(), ket.strip(), jenis))
        jid = c.lastrowid
        if not bukti.strip():
            c.execute("UPDATE jurnal SET bukti=%s WHERE id=%s", (f"{prefix}-{jid:04d}", jid))
        for kode, d, k in bersih:
            c.execute("INSERT INTO jurnal_detail (jurnal_id,kode,debit,kredit) VALUES (%s,%s,%s,%s)", (jid, kode, d, k))


def hapus_jurnal(jid):
    with db.cursor(commit=True) as c:
        c.execute("SELECT sumber FROM jurnal WHERE id=%s", (jid,))
        r = c.fetchone()
        if not r:
            raise ValueError("Jurnal tidak ditemukan.")
        if r["sumber"] != "MANUAL":
            raise ValueError("Jurnal ini dibuat otomatis dari modul Persediaan. Hapus lewat halaman Persediaan.")
        c.execute("DELETE FROM jurnal WHERE id=%s", (jid,))


def hitung_jurnal():
    with db.cursor() as c:
        c.execute("SELECT jenis, COUNT(*) n FROM jurnal GROUP BY jenis")
        return {r["jenis"]: r["n"] for r in c.fetchall()}


def simpan_penutup(buku):
    ent, _, _ = buku.penutup()
    with db.cursor(commit=True) as c:
        c.execute("DELETE FROM jurnal WHERE jenis='PNT'")
        for e in ent:
            c.execute("INSERT INTO jurnal (tanggal,bukti,keterangan,jenis,sumber) VALUES (%s,%s,%s,'PNT','SISTEM')",
                      (e["tanggal"], f"JP-{e['no']:02d}", e["ket"]))
            jid = c.lastrowid
            for r in e["baris"]:
                c.execute("INSERT INTO jurnal_detail (jurnal_id,kode,debit,kredit) VALUES (%s,%s,%s,%s)",
                          (jid, r["kode"], r["d"], r["k"]))
    return len(ent)
