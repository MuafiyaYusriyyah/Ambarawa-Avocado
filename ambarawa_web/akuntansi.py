"""Mesin akuntansi: format angka, simpan data, dan semua tabel laporan.
Setiap laporan adalah fungsi yang mengembalikan (kolom, baris) sehingga layar dan Excel memakai data yang sama.
Sumber data hanya tiga: saldo awal, jurnal umum (JU), dan jurnal penyesuaian (AJP)."""
import datetime as dt
from collections import defaultdict
from decimal import Decimal as D, InvalidOperation

from db import ambil, cursor

Z = D(0)
LR = ("Pendapatan", "Pembelian", "HPP", "Beban")        # kelompok akun yang masuk kolom laba rugi
MODAL, PRIVE, IKHTISAR, LAIN = "3-101", "3-102", "3-103", "4-104"
STOK = {"1-104": "Alpukat Segar", "1-105": "Alpukat Frozen"}
BULAN = "Jan Feb Mar Apr Mei Jun Jul Agu Sep Okt Nov Des".split()


# ------------------------------------------------------------------ format dan baca input
def dec(v):
    return D(str(v)) if v not in (None, "") else Z


def rp(v, nol="-"):
    v = dec(v)
    if v == 0:
        return nol
    s = f"{abs(v):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    s = s[:-3] if s.endswith(",00") else s
    return f"({s})" if v < 0 else s


def tgl(v):
    return f"{v.day:02d} {BULAN[v.month - 1]} {v.year}" if v else ""


def angka(s, uang=True):
    """'1.500.000', '1500000', '1500,50' -> Decimal. Angka (int, float, Decimal) langsung dikonversi."""
    if isinstance(s, (int, float, D)):
        return D(str(round(s, 2)))
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


def tanggal_teks(v):
    return v.strftime("%d-%m-%Y")


def tanggal(s):
    for f in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime((s or "").strip(), f).date()
        except ValueError:
            pass
    raise ValueError("Tanggal tidak valid. Tulis HH-BB-TTTT, contoh 31-12-2026.")


# ------------------------------------------------------------------ simpan data
def akun_awal():
    return ambil("SELECT a.kode,a.nama,a.saldo_normal,s.debit,s.kredit,s.qty FROM akun a LEFT JOIN saldo_awal s ON s.kode=a.kode "
                 "WHERE a.kelompok IN ('Aset','Liabilitas') OR a.kode='3-101' ORDER BY a.kode")


def simpan_saldo_awal(isian):
    """isian {kode: (saldo, kg)} -> (total debit, total kredit)."""
    data, td, tk = [], Z, Z
    for a in akun_awal():
        v, q = angka(isian[a["kode"]][0]), angka(isian[a["kode"]][1], False)
        if v < 0 or q < 0:
            raise ValueError(f"Nilai negatif pada {a['nama']} tidak diperbolehkan.")
        d, k = (v, Z) if a["saldo_normal"] == "D" else (Z, v)
        td, tk = td + d, tk + k
        data.append((a["kode"], d, k, q))
    with cursor(True) as c:
        for x in data:
            c.execute("INSERT INTO saldo_awal (kode,debit,kredit,qty) VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE "
                      "debit=VALUES(debit),kredit=VALUES(kredit),qty=VALUES(qty)", x)
    return td, tk


def simpan_jurnal(jenis, prefix, tgl_s, bukti, ket, baris):
    """baris: [(kode, debit, kredit)] berupa teks. Jurnal harus seimbang."""
    t, bersih = tanggal(tgl_s), []
    for kode, d, k in baris:
        d, k = angka(d), angka(k)
        if d < 0 or k < 0 or (d and k):
            raise ValueError("Tiap baris hanya boleh diisi di debit atau kredit, dan tidak boleh negatif.")
        if d or k:
            if not kode:
                raise ValueError("Ada nominal yang akunnya belum dipilih.")
            bersih.append((kode, d, k))
    if len(bersih) < 2:
        raise ValueError("Jurnal minimal terdiri dari dua baris akun.")
    td, tk = sum(x[1] for x in bersih), sum(x[2] for x in bersih)
    if td != tk:
        raise ValueError(f"Jurnal belum seimbang: debit {rp(td)}, kredit {rp(tk)}.")
    with cursor(True) as c:
        c.execute("INSERT INTO jurnal (tanggal,bukti,keterangan,jenis,sumber) VALUES (%s,%s,%s,%s,'MANUAL')",
                  (t, bukti.strip(), ket.strip(), jenis))
        jid = c.lastrowid
        if not bukti.strip():
            c.execute("UPDATE jurnal SET bukti=%s WHERE id=%s", (f"{prefix}-{jid:04d}", jid))
        for x in bersih:
            c.execute("INSERT INTO jurnal_detail (jurnal_id,kode,debit,kredit) VALUES (%s,%s,%s,%s)", (jid, *x))


def hapus_jurnal(jid):
    r = ambil("SELECT sumber FROM jurnal WHERE id=%s", jid)
    if not r:
        raise ValueError("Jurnal tidak ditemukan.")
    if r[0]["sumber"] != "MANUAL":
        raise ValueError("Jurnal ini dibuat otomatis dari Persediaan. Hapus lewat halaman Persediaan.")
    with cursor(True) as c:
        c.execute("DELETE FROM jurnal WHERE id=%s", (jid,))


def tambah_akun(kode, nama, kelompok, normal):
    kode, nama = kode.strip(), nama.strip()
    if not kode or not nama:
        raise ValueError("Kode dan nama akun wajib diisi.")
    if ambil("SELECT kode FROM akun WHERE kode=%s", kode):
        raise ValueError("Kode akun sudah dipakai.")
    with cursor(True) as c:
        c.execute("INSERT INTO akun (kode,nama,kelompok,saldo_normal) VALUES (%s,%s,%s,%s)", (kode, nama, kelompok, normal))


def simpan_periode(usaha, periode, awal, akhir):
    a, b = tanggal(awal), tanggal(akhir)
    if b < a:
        raise ValueError("Tanggal akhir tidak boleh sebelum tanggal awal.")
    with cursor(True) as c:
        c.execute("UPDATE pengaturan SET nama_usaha=%s,nama_periode=%s,tgl_awal=%s,tgl_akhir=%s WHERE id=1",
                  (usaha.strip() or "Ambarawa Avocado", periode.strip(), a, b))


def simpan_penutup():
    b = Buku()
    ent = b.penutup()
    with cursor(True) as c:
        c.execute("DELETE FROM jurnal WHERE jenis='PNT'")
        for i, (ket, baris) in enumerate(ent, 1):
            c.execute("INSERT INTO jurnal (tanggal,bukti,keterangan,jenis,sumber) VALUES (%s,%s,%s,'PNT','SISTEM')",
                      (b.pg["tgl_akhir"], f"JP-{i:02d}", ket))
            jid = c.lastrowid
            for kode, _, d, k in baris:
                c.execute("INSERT INTO jurnal_detail (jurnal_id,kode,debit,kredit) VALUES (%s,%s,%s,%s)", (jid, kode, d, k))
    return len(ent)


# ------------------------------------------------------------------ bentuk tabel
# kolom: (judul, lebar, rata)   baris: (isi sel, tag, iid)   tag "b" = tebal, "kosong" = pesan kosong
def kol(*spek):
    return [(j, w, r) for j, w, r in spek]


KOL_BB = kol(("Tanggal", 105, "w"), ("Keterangan", 430, "w"), ("Bukti", 90, "w"), ("Debit", 140, "e"), ("Kredit", 140, "e"), ("Saldo", 160, "e"))
KOL_SALDO = kol(("Kode", 90, "w"), ("Nama Akun", 420, "w"), ("Debit", 180, "e"), ("Kredit", 180, "e"))
KOL_LAP = kol(("Keterangan", 520, "w"), ("Rincian", 170, "e"), ("Jumlah", 170, "e"))
KOL_NL = kol(("Kode", 70, "w"), ("Nama Akun", 250, "w"), *[(n, 112, "e") for n in (
    "NS Debit", "NS Kredit", "Penyesuaian D", "Penyesuaian K", "Disesuaikan D", "Disesuaikan K", "Laba Rugi D", "Laba Rugi K", "Neraca D", "Neraca K")])
KOL_JURNAL = kol(("Tanggal", 105, "w"), ("Bukti", 90, "w"), ("Keterangan / Akun", 430, "w"), ("Ref", 70, "w"), ("Debit", 140, "e"), ("Kredit", 140, "e"))
KOL_PNT = kol(("Tanggal", 105, "w"), ("Keterangan / Akun", 520, "w"), ("Ref", 80, "w"), ("Debit", 150, "e"), ("Kredit", 150, "e"))
KOL_KARTU = kol(("Tanggal", 100, "w"), ("Keterangan", 300, "w"), ("Mutasi", 70, "w"), ("Jumlah kg", 90, "e"), ("Harga/kg", 100, "e"),
                ("Nilai (Rp)", 120, "e"), ("Saldo kg", 90, "e"), ("Saldo Rp", 130, "e"))
KOL_AWAL = kol(("Kode", 90, "w"), ("Nama Akun", 380, "w"), ("Debit", 170, "e"), ("Kredit", 170, "e"), ("Jumlah (kg)", 110, "e"))
KOL_AKUN = kol(("Kode", 90, "w"), ("Nama Akun", 380, "w"), ("Kelompok", 140, "w"), ("Saldo Normal", 120, "w"))
I = "      "


def B(*sel, tag=None):
    return list(sel), tag


def sisi(n):
    """saldo bersih (debit - kredit) -> (debit, kredit)"""
    return (n, Z) if n > 0 else (Z, abs(n))


class Buku:
    """Memuat data sekali, lalu menghitung seluruh siklus dari saldo awal + jurnal."""

    def __init__(self):
        self.akun = ambil("SELECT * FROM akun ORDER BY kode")
        self.a = {x["kode"]: x for x in self.akun}
        self.sa = {x["kode"]: (dec(x["debit"]), dec(x["kredit"]), dec(x["qty"])) for x in ambil("SELECT * FROM saldo_awal")}
        self.pg = ambil("SELECT * FROM pengaturan WHERE id=1")[0]
        self.baris = [dict(x, debit=dec(x["debit"]), kredit=dec(x["kredit"])) for x in ambil(
            "SELECT j.tanggal,j.bukti,j.keterangan,j.jenis,d.kode,d.debit,d.kredit FROM jurnal j "
            "JOIN jurnal_detail d ON d.jurnal_id=j.id WHERE j.jenis IN ('JU','AJP') ORDER BY j.tanggal,j.id,d.id")]
        self._lap = None

    def mut(self, jenis):
        m = defaultdict(lambda: [Z, Z])
        for l in self.baris:
            if l["jenis"] in jenis:
                m[l["kode"]][0] += l["debit"]
                m[l["kode"]][1] += l["kredit"]
        return m

    def net(self, jenis):
        """Saldo bersih (debit - kredit) tiap akun = saldo awal + mutasi jurnal."""
        m = self.mut(jenis)
        return {k: self.sa.get(k, (Z, Z, Z))[0] - self.sa.get(k, (Z, Z, Z))[1] + m[k][0] - m[k][1] for k in self.a}

    # ---- 2. buku besar: satu tabel untuk semua akun
    def buku_besar(self, jenis=("JU",)):
        per = defaultdict(list)
        for l in self.baris:
            if l["jenis"] in jenis:
                per[l["kode"]].append((l["tanggal"], l["keterangan"], l["bukti"], l["debit"], l["kredit"], l["jenis"]))
        rows = []
        for a in self.akun:
            d0, k0, _ = self.sa.get(a["kode"], (Z, Z, Z))
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

    # ---- 3 dan 9. neraca saldo (sebelum penyesuaian) / neraca saldo akhir (setelah penutup)
    def net_akhir(self):
        n, ma = self.net(("JU", "AJP")), self.lap()["modal_akhir"]
        for k, a in self.a.items():
            if a["kelompok"] in LR:
                n[k] = Z
        n[PRIVE] = n[IKHTISAR] = Z
        n[MODAL] = -ma
        return n

    def saldo(self, akhir=False):
        net = self.net_akhir() if akhir else self.net(("JU",))
        rows, td, tk = [], Z, Z
        for a in self.akun:
            d, k = sisi(net[a["kode"]])
            if d or k:
                rows.append(B(a["kode"], a["nama"], d, k))
                td, tk = td + d, tk + k
        return KOL_SALDO, rows + [B("", "TOTAL", td, tk, tag="b")]

    # ---- 6. neraca lajur
    def neraca_lajur(self):
        ns, aj = self.net(("JU",)), self.mut(("AJP",))
        rows, tot = [], [Z] * 10
        for a in self.akun:
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

    # ---- 7. laporan keuangan
    def lap(self):
        if self._lap:
            return self._lap
        net = self.net(("JU", "AJP"))
        nat = lambda k: net[k] if self.a[k]["saldo_normal"] == "D" else -net[k]

        def grup(f, mentah=False):
            return [(a["kode"], a["nama"], net[a["kode"]] if mentah else nat(a["kode"]), a["saldo_normal"])
                    for a in self.akun if f(a) and net[a["kode"]]]
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
        d0, k0, _ = self.sa.get(MODAL, (Z, Z, Z))
        md, mk = self.mut(("JU", "AJP"))[MODAL]
        p["modal_awal"], p["tambah"], p["prive"] = k0 - d0, mk - md, nat(PRIVE)
        p["modal_akhir"] = p["modal_awal"] + p["tambah"] + p["laba"] - p["prive"]
        p["t_lancar"], p["t_tetap"], p["t_liab"] = jml(p["lancar"]), jml(p["tetap"]), jml(p["liab"])
        self._lap = p
        return p

    def laba_rugi(self):
        p = self.lap()
        r = [B("Pendapatan", tag="b")] + [B(I + n, j) for _, n, j, _ in p["pend"]] + [B(I + "(-) " + n, j) for _, n, j, _ in p["poto"]]
        r += [B("Penjualan Bersih", None, p["pen_bersih"], tag="b"), B("Harga Pokok Penjualan", tag="b")]
        r += [B(I + ("(-) " if m == "K" else "") + n, j) for _, n, j, m in p["beli"]] + [B(I + n, j) for _, n, j, _ in p["hpp"]]
        r += [B("Total Harga Pokok Penjualan", None, p["total_hpp"], tag="b"), B("LABA KOTOR", None, p["kotor"], tag="b"), B("Beban Operasional", tag="b")]
        r += [B(I + n, j) for _, n, j, _ in p["beban"]]
        r += [B("Total Beban Operasional", None, p["total_beban"], tag="b"), B("LABA USAHA", None, p["usaha"], tag="b")]
        r += [B(n, None, j) for _, n, j, _ in p["lain"]]
        return KOL_LAP, r + [B("LABA BERSIH" if p["laba"] >= 0 else "RUGI BERSIH", None, p["laba"], tag="b")]

    def ekuitas(self):
        p = self.lap()
        return KOL_LAP, [B("Modal Pemilik, awal periode", None, p["modal_awal"]), B(I + "Penambahan modal", None, p["tambah"]),
                         B(I + ("Laba" if p["laba"] >= 0 else "Rugi") + " bersih periode berjalan", None, p["laba"]),
                         B(I + "Prive", None, -p["prive"]), B("MODAL PEMILIK, AKHIR PERIODE", None, p["modal_akhir"], tag="b")]

    def posisi(self):
        p = self.lap()
        r = [B("ASET", tag="b"), B("Aset Lancar", tag="b")] + [B(I + n, j) for _, n, j, _ in p["lancar"]]
        r += [B("Total Aset Lancar", None, p["t_lancar"], tag="b"), B("Aset Tetap", tag="b")] + [B(I + n, j) for _, n, j, _ in p["tetap"]]
        r += [B("Total Aset Tetap", None, p["t_tetap"], tag="b"), B("TOTAL ASET", None, p["t_lancar"] + p["t_tetap"], tag="b"), B("LIABILITAS", tag="b")]
        r += [B(I + n, j) for _, n, j, _ in p["liab"]]
        return KOL_LAP, r + [B("Total Liabilitas", None, p["t_liab"], tag="b"), B("EKUITAS", tag="b"), B(I + "Modal Pemilik", p["modal_akhir"]),
                             B("TOTAL LIABILITAS + EKUITAS", None, p["t_liab"] + p["modal_akhir"], tag="b")]

    # ---- 8. jurnal penutup
    def penutup(self):
        net = self.net(("JU", "AJP"))
        nm = lambda k: self.a[k]["nama"]
        sem = [a for a in self.akun if a["kelompok"] in LR and net[a["kode"]]]
        kr, db_ = [a for a in sem if net[a["kode"]] < 0], [a for a in sem if net[a["kode"]] > 0]
        ent = []
        if kr:
            ent.append(("Menutup akun pendapatan ke Ikhtisar Laba Rugi", [(a["kode"], a["nama"], -net[a["kode"]], Z) for a in kr]
                        + [(IKHTISAR, nm(IKHTISAR), Z, -sum(net[a["kode"]] for a in kr))]))
        if db_:
            ent.append(("Menutup akun HPP dan beban ke Ikhtisar Laba Rugi", [(IKHTISAR, nm(IKHTISAR), sum(net[a["kode"]] for a in db_), Z)]
                        + [(a["kode"], a["nama"], Z, net[a["kode"]]) for a in db_]))
        laba = -sum(net[a["kode"]] for a in sem)
        if laba > 0:
            ent.append(("Menutup Ikhtisar Laba Rugi (laba) ke Modal Pemilik", [(IKHTISAR, nm(IKHTISAR), laba, Z), (MODAL, nm(MODAL), Z, laba)]))
        elif laba < 0:
            ent.append(("Menutup Ikhtisar Laba Rugi (rugi) ke Modal Pemilik", [(MODAL, nm(MODAL), -laba, Z), (IKHTISAR, nm(IKHTISAR), Z, -laba)]))
        if net[PRIVE] > 0:
            ent.append(("Menutup Prive ke Modal Pemilik", [(MODAL, nm(MODAL), net[PRIVE], Z), (PRIVE, nm(PRIVE), Z, net[PRIVE])]))
        return ent

    def tabel_penutup(self):
        rows, td, tk = [], Z, Z
        for i, (ket, baris) in enumerate(self.penutup(), 1):
            rows.append(B(self.pg["tgl_akhir"], f"{i}. {ket}", tag="b"))
            for kode, nama, d, k in baris:
                rows.append(B("", (I if k else "") + nama, kode, d, k))
                td, tk = td + d, tk + k
        return KOL_PNT, (rows or [B("", "Belum ada akun sementara yang bersaldo.", tag="kosong")]) + [B("", "TOTAL JURNAL PENUTUP", "", td, tk, tag="b")]

    # ---- tabel pendukung
    def tabel_awal(self):
        rows, td, tk = [], Z, Z
        for a in self.akun:
            d, k, q = self.sa.get(a["kode"], (Z, Z, Z))
            if d or k:
                rows.append(B(a["kode"], a["nama"], d, k, q if a["kode"] in STOK else None))
                td, tk = td + d, tk + k
        return KOL_AWAL, rows + [B("", "TOTAL", td, tk, None, tag="b")]

    def tabel_akun(self):
        return KOL_AKUN, [B(a["kode"], a["nama"], a["kelompok"], "Debit" if a["saldo_normal"] == "D" else "Kredit") for a in self.akun]


def tabel_jurnal(jenis):
    """Daftar jurnal satu jenis (JU / AJP) lengkap dengan total debit dan kredit."""
    rows, td, tk, sudah = [], Z, Z, set()
    for r in ambil("SELECT j.id,j.tanggal,j.bukti,j.keterangan,j.sumber,d.kode,a.nama,d.debit,d.kredit FROM jurnal j "
                   "JOIN jurnal_detail d ON d.jurnal_id=j.id JOIN akun a ON a.kode=d.kode WHERE j.jenis=%s "
                   "ORDER BY j.tanggal,j.id,d.id", jenis):
        d, k = dec(r["debit"]), dec(r["kredit"])
        td, tk = td + d, tk + k
        if r["id"] not in sudah:
            sudah.add(r["id"])
            rows.append(([r["tanggal"], r["bukti"], (r["keterangan"] or "") + ("" if r["sumber"] == "MANUAL" else "   [otomatis]")], "b", f"j{r['id']}_{len(rows)}"))
        rows.append((["", "", (I if k else "") + r["nama"], r["kode"], d, k], None, f"j{r['id']}_{len(rows)}"))
    if not rows:
        rows = [B("", "", "Belum ada jurnal. Catat lewat tombol Input di Beranda.", tag="kosong")]
    return KOL_JURNAL, rows + [B("", "", "TOTAL", "", td, tk, tag="b")]


def tabel_nota(tipe):
    """Daftar nota penjualan (JUAL) atau pembelian (BELI)."""
    pihak = "Customer" if tipe == "JUAL" else "Supplier"
    kolom = kol(("Tanggal", 105, "w"), ("No. Nota", 110, "w"), (pihak, 200, "w"), ("Jenis", 170, "w"), ("Jumlah kg", 90, "e"),
                ("Harga/kg", 110, "e"), ("Total (Rp)", 140, "e"), ("Pembayaran", 150, "w"))
    rows, tq, tt = [], Z, Z
    for r in ambil("SELECT * FROM nota WHERE tipe=%s ORDER BY tanggal,id", tipe):
        q, t = dec(r["qty"]), dec(r["total"])
        tq, tt = tq + q, tt + t
        rows.append(B(r["tanggal"], r["no_nota"], r["pihak"], r["jenis"], q, dec(r["harga"]), t, r["cara"]))
    return kolom, (rows or [B("", "Belum ada nota.", tag="kosong")]) + [B("", "TOTAL", "", "", tq, None, tt, "", tag="b")]


def tabel_kartu(kode):
    """Kartu stok persediaan (rata-rata bergerak). iid baris terakhir = id jurnal, dipakai untuk hapus."""
    s = ambil("SELECT debit,kredit,qty FROM saldo_awal WHERE kode=%s", kode)
    q, n = (dec(s[0]["qty"]), dec(s[0]["debit"]) - dec(s[0]["kredit"])) if s else (Z, Z)
    rows = [B(None, "Persediaan awal", "Awal", q, n / q if q else Z, n, q, n)] if q or n else []
    mut = ambil("SELECT * FROM persediaan_mutasi WHERE kode=%s ORDER BY id", kode)
    for i, m in enumerate(mut):
        t = 1 if m["jenis"] == "MASUK" else -1
        q, n = q + t * dec(m["qty"]), n + t * dec(m["total"])
        rows.append(([m["tanggal"], m["keterangan"], m["jenis"].capitalize(), dec(m["qty"]), dec(m["harga"]), dec(m["total"]), q, n],
                     None, str(m["jurnal_id"]) if i == len(mut) - 1 else None))
    return KOL_KARTU, (rows or [B("", "Belum ada mutasi.", tag="kosong")]) + [B("", "Saldo kartu stok", "", None, None, None, q, n, tag="b")]


# nama tabel -> fungsi(buku). Dipakai halaman layar dan ekspor Excel.
TABEL = {"jual": lambda b: tabel_nota("JUAL"), "beli": lambda b: tabel_nota("BELI"), "ju": lambda b: tabel_jurnal("JU"), "ajp": lambda b: tabel_jurnal("AJP"), "bb": lambda b: b.buku_besar(("JU",)),
         "bb_ajp": lambda b: b.buku_besar(("JU", "AJP")), "ns": lambda b: b.saldo(), "nsa": lambda b: b.saldo(True),
         "nl": lambda b: b.neraca_lajur(), "lr": lambda b: b.laba_rugi(), "ek": lambda b: b.ekuitas(), "pos": lambda b: b.posisi(),
         "pnt": lambda b: b.tabel_penutup(), "awal": lambda b: b.tabel_awal(), "akun": lambda b: b.tabel_akun(),
         "k104": lambda b: tabel_kartu("1-104"), "k105": lambda b: tabel_kartu("1-105")}
