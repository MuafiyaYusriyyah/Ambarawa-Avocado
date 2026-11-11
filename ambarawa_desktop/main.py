"""Ambarawa Avocado - Aplikasi Siklus Akuntansi (Python desktop + MySQL).
Jalankan:  python main.py
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import akuntansi as ak
import db
import export
import layanan as ly
import persediaan as psd
from tampilan import (C, F, FB, FH2, GulungFrame, Halaman, Tabel, aman, gaya, isian, kartu, label,
                      pilihan, tombol)


def warnai(lbl, ok, teks_ok, teks_err=None):
    """Label status: hijau + teks_ok bila ok, merah + teks_err bila tidak."""
    lbl.config(text=teks_ok if (ok or teks_err is None) else teks_err, fg=C["hijau_ok"] if ok else C["merah"])


def r(v, nol=""):
    return ly.rp(v, nol)


def kepala_kolom(induk, spek):
    """Baris judul kolom hijau untuk form berbentuk baris (saldo awal, jurnal)."""
    f = tk.Frame(induk, bg=C["daun"])
    for teks, lebar, rata in spek:
        tk.Label(f, text=teks, width=lebar, anchor=rata, font=FB, fg="#ffffff", bg=C["daun"], pady=6, padx=6).pack(side="left", padx=(0, 6))
    return f


# =================================================================== BERANDA
class Beranda(Halaman):
    judul = "Beranda"

    def bangun(self):
        k = kartu(self.badan)
        k.pack(fill="x")
        label(k, "Input data", FH2).pack(anchor="w", pady=(0, 8))
        bar = tk.Frame(k, bg=C["kertas"])
        bar.pack(fill="x")
        for teks, kunci in (("Input Saldo Awal", "in_saldo"), ("Input Jurnal Umum", "in_ju"),
                            ("Input Jurnal Penyesuaian", "in_ajp"), ("Input Persediaan", "in_psd")):
            tombol(bar, teks, lambda x=kunci: self.app.show(x)).pack(side="left", padx=(0, 10))

        bawah = tk.Frame(self.badan, bg=C["krim"])
        bawah.pack(fill="both", expand=True, pady=(14, 0))
        bawah.columnconfigure(0, weight=3)
        bawah.columnconfigure(1, weight=2)
        bawah.rowconfigure(0, weight=1)
        alur = kartu(bawah)
        alur.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        label(alur, "Alur siklus", FH2).pack(anchor="w", pady=(0, 8))
        self.isi_alur = tk.Frame(alur, bg=C["kertas"])
        self.isi_alur.pack(fill="both", expand=True)

        form = kartu(bawah)
        form.grid(row=0, column=1, sticky="nsew")
        label(form, "Periode", FH2).pack(anchor="w", pady=(0, 4))
        self.v = {x: tk.StringVar() for x in ("usaha", "periode", "awal", "akhir")}
        for key, teks in (("usaha", "Nama usaha"), ("periode", "Nama periode"),
                          ("awal", "Tanggal awal (HH-BB-TTTT)"), ("akhir", "Tanggal akhir (HH-BB-TTTT)")):
            label(form, teks, FB).pack(anchor="w", pady=(8, 2))
            isian(form, self.v[key], 30).pack(fill="x", ipady=3)
        tombol(form, "Simpan periode", self.simpan).pack(anchor="w", pady=(14, 0))

    @aman
    def simpan(self):
        v = self.v
        ly.simpan_pengaturan(v["usaha"].get(), v["periode"].get(), v["awal"].get(), v["akhir"].get())
        messagebox.showinfo("Tersimpan", "Periode disimpan.")
        self.segarkan()

    @aman
    def segarkan(self):
        b = ak.muat()
        cnt, pg = ly.hitung_jurnal(), ly.pengaturan()
        self.v["usaha"].set(pg["nama_usaha"])
        self.v["periode"].set(pg["nama_periode"])
        self.v["awal"].set(ly.tgl_input(pg["tgl_awal"]))
        self.v["akhir"].set(ly.tgl_input(pg["tgl_akhir"]))
        _, td, tk_ = b.neraca_saldo()
        langkah = [
            ("saldo_awal", "Saldo awal", "sudah terisi" if b.awal_sudah_diisi() else "belum diisi", b.awal_sudah_diisi()),
            ("ju", "Jurnal umum", f"{cnt.get('JU', 0)} jurnal", bool(cnt.get("JU"))),
            ("bb", "Buku besar", "otomatis", True),
            ("ns", "Neraca saldo", "seimbang" if td == tk_ and td != 0 else "menunggu data", td == tk_ and td != 0),
            ("ajp", "Jurnal penyesuaian", f"{cnt.get('AJP', 0)} jurnal", bool(cnt.get("AJP"))),
            ("nl", "Neraca lajur", "otomatis", True),
            ("lap", "Laporan keuangan", "otomatis", True),
            ("pnt", "Jurnal penutup", "tersimpan" if cnt.get("PNT") else "belum disimpan", bool(cnt.get("PNT"))),
        ]
        for w in self.isi_alur.winfo_children():
            w.destroy()
        for kunci, teks, ket, selesai in langkah:
            baris = tk.Frame(self.isi_alur, bg=C["kertas"])
            baris.pack(fill="x", pady=3)
            tk.Label(baris, text="●" if selesai else "○", font=("Segoe UI", 12),
                     fg=C["daun"] if selesai else C["tanah"], bg=C["kertas"]).pack(side="left")
            ln = tk.Label(baris, text=teks, font=FB, fg=C["daun"], bg=C["kertas"], cursor="hand2")
            ln.pack(side="left", padx=8)
            ln.bind("<Button-1>", lambda e, x=kunci: self.app.show(x))
            tk.Label(baris, text=ket, font=("Segoe UI", 9), fg=C["tanah"], bg=C["kertas"]).pack(side="right")


# =================================================================== DAFTAR AKUN (tetap ada input)
class DaftarAkun(Halaman):
    judul = "Daftar Akun"

    def bangun(self):
        k = kartu(self.badan)
        k.pack(fill="x", pady=(0, 12))
        self.v = {x: tk.StringVar() for x in ("kode", "nama", "kel", "normal")}
        label(k, "Kode", FB).grid(row=0, column=0, sticky="w")
        isian(k, self.v["kode"], 10).grid(row=1, column=0, padx=(0, 10), ipady=3)
        label(k, "Nama akun", FB).grid(row=0, column=1, sticky="w")
        isian(k, self.v["nama"], 32).grid(row=1, column=1, padx=(0, 10), ipady=3)
        label(k, "Kelompok", FB).grid(row=0, column=2, sticky="w")
        self.v["kel"].set("Aset")
        pilihan(k, self.v["kel"], ["Aset", "Liabilitas", "Ekuitas", "Pendapatan", "Pembelian", "HPP", "Beban"], 12).grid(row=1, column=2, padx=(0, 10))
        label(k, "Saldo normal", FB).grid(row=0, column=3, sticky="w")
        self.v["normal"].set("Debit")
        pilihan(k, self.v["normal"], ["Debit", "Kredit"], 8).grid(row=1, column=3, padx=(0, 10))
        tombol(k, "Tambah akun", self.tambah).grid(row=1, column=4)
        self.tb = Tabel(self.badan, [("Kode", 90, "w"), ("Nama Akun", 380, "w"), ("Kelompok", 140, "w"), ("Saldo Normal", 120, "w")], tinggi=18)
        self.tb.pack(fill="both", expand=True)

    @aman
    def tambah(self):
        v = self.v
        ly.tambah_akun(v["kode"].get(), v["nama"].get(), v["kel"].get(), "D" if v["normal"].get() == "Debit" else "K")
        v["kode"].set("")
        v["nama"].set("")
        self.segarkan()

    @aman
    def segarkan(self):
        self.tb.isi([((a["kode"], a["nama"], a["kelompok"], "Debit" if a["saldo_normal"] == "D" else "Kredit"), None, None)
                     for a in ly.daftar_akun()])


# =================================================================== SALDO AWAL
class SaldoAwalLihat(Halaman):
    judul = "Saldo Awal"

    def bangun(self):
        self.tb = Tabel(self.badan, [("Kode", 90, "w"), ("Nama Akun", 380, "w"), ("Debit", 170, "e"), ("Kredit", 170, "e"), ("Jumlah (kg)", 110, "e")], tinggi=20)
        self.tb.pack(fill="both", expand=True)
        self.st = tk.Label(self.badan, font=FB, bg=C["krim"])
        self.st.pack(anchor="w", pady=(8, 0))

    @aman
    def segarkan(self):
        rows, td, tk_ = [], ly.Z, ly.Z
        for a in ly.akun_saldo_awal():
            d, k = ly.dec_(a["debit"]), ly.dec_(a["kredit"])
            if d or k:
                td, tk_ = td + d, tk_ + k
                rows.append(((a["kode"], a["nama"], r(d), r(k), ly.kg(a["qty"]) if a["kode"] in psd.STOK and a["qty"] else ""), None, None))
        if not rows:
            rows = [(("", "Belum ada saldo awal. Isi lewat tombol Input Saldo Awal di Beranda.", "", "", ""), "kosong", None)]
        rows.append((("", "TOTAL", r(td, "0"), r(tk_, "0"), ""), "jumlah", None))
        self.tb.isi(rows)
        warnai(self.st, td == tk_, "✔ Seimbang", f"✖ Belum seimbang, selisih Rp {ly.rp(td - tk_)}")


class InputSaldoAwal(Halaman):
    judul = "Input Saldo Awal"
    kembali = True

    def bangun(self):
        k = kartu(self.badan, padx=10, pady=10)
        k.pack(fill="both", expand=True)
        kepala_kolom(k, (("Kode", 8, "w"), ("Nama Akun", 34, "w"), ("Sisi", 8, "w"), ("Saldo (Rp)", 20, "e"), ("Jumlah (kg)", 14, "e"))).pack(fill="x")
        self.gulung = GulungFrame(k)
        self.gulung.pack(fill="both", expand=True)
        self.isian_, self.akun = {}, []
        pie = tk.Frame(k, bg=C["lime"], padx=10, pady=8)
        pie.pack(fill="x")
        self.t_d, self.t_k, self.t_s = (tk.Label(pie, font=FB, bg=C["lime"], fg=C["daun"]) for _ in range(3))
        for lbl in (self.t_d, self.t_k, self.t_s):
            lbl.pack(side="left", padx=(0, 28))
        tombol(pie, "Simpan saldo awal", self.simpan).pack(side="right")

    def _hitung(self, *_):
        d = k = ly.Z
        for a in self.akun:
            try:
                v = ly.angka(self.isian_[a["kode"]][0].get())
            except ValueError:
                v = ly.Z
            if a["saldo_normal"] == "D":
                d += v
            else:
                k += v
        self.t_d.config(text="Total debit: " + ly.rp(d, "0"))
        self.t_k.config(text="Total kredit: " + ly.rp(k, "0"))
        self.t_s.config(text="Selisih: " + ly.rp(d - k, "0"), fg=C["hijau_ok"] if d == k else C["merah"])

    @aman
    def segarkan(self):
        self.akun = ly.akun_saldo_awal()
        for w in self.gulung.isi.winfo_children():
            w.destroy()
        self.isian_ = {}
        for n, a in enumerate(self.akun):
            bg = C["kertas"] if n % 2 == 0 else "#f7f8f5"
            f = tk.Frame(self.gulung.isi, bg=bg)
            f.pack(fill="x")
            for teks, lebar in ((a["kode"], 8), (a["nama"], 34), ("Debit" if a["saldo_normal"] == "D" else "Kredit", 8)):
                tk.Label(f, text=teks, width=lebar, anchor="w", font=F, bg=bg, fg=C["teks"], padx=6, pady=4).pack(side="left")
            normal = a["debit"] if a["saldo_normal"] == "D" else a["kredit"]
            vs = tk.StringVar(value=ly.polos(normal))
            vs.trace_add("write", self._hitung)
            isian(f, vs, 20, justify="right").pack(side="left", padx=6, pady=3, ipady=2)
            vq = tk.StringVar(value=ly.polos(a["qty"]))
            if a["kode"] in psd.STOK:
                isian(f, vq, 14, justify="right").pack(side="left", padx=6)
            self.isian_[a["kode"]] = (vs, vq)
        self._hitung()

    @aman
    def simpan(self):
        td, tk_ = ly.simpan_saldo_awal({k: (v[0].get(), v[1].get()) for k, v in self.isian_.items()})
        if td == tk_:
            messagebox.showinfo("Tersimpan", "Saldo awal disimpan dan seimbang.")
        else:
            messagebox.showwarning("Belum seimbang", f"Saldo awal disimpan, tetapi belum seimbang (selisih Rp {ly.rp(td - tk_)}). Periksa kembali.")
        return True


# =================================================================== JURNAL: daftar (siklus) dan input (beranda)
class JurnalDaftar(Halaman):
    judul = "Jurnal Umum"
    jenis, nama = "JU", "Jurnal Umum"

    def bangun(self):
        bar = tk.Frame(self.badan, bg=C["krim"])
        bar.pack(fill="x", pady=(0, 8))
        tombol(bar, "Hapus jurnal terpilih", self.hapus, "bahaya").pack(side="left")
        self.st = tk.Label(bar, font=FB, bg=C["krim"])
        self.st.pack(side="right")
        self.tb = Tabel(self.badan, [("Tanggal", 105, "w"), ("Bukti", 90, "w"), ("Keterangan / Akun", 430, "w"),
                                     ("Ref", 70, "w"), ("Debit", 140, "e"), ("Kredit", 140, "e")], tinggi=22)
        self.tb.pack(fill="both", expand=True)

    @aman
    def segarkan(self):
        daftar, td, tk_ = ak.daftar_jurnal(self.jenis)
        rows = []
        for j in daftar:
            oto = "" if j["sumber"] == "MANUAL" else "   [otomatis]"
            rows.append(((ly.tgl(j["tanggal"]), j["bukti"], (j["ket"] or "") + oto, "", "", ""), "kepala", f"j{j['id']}"))
            for n, b in enumerate(j["baris"]):
                rows.append((("", "", ("      " if b["k"] else "") + b["nama"], b["kode"], r(b["d"]), r(b["k"])), None, f"j{j['id']}_{n}"))
        if not rows:
            rows.append((("", "", f"Belum ada {self.nama.lower()}. Catat lewat tombol Input di Beranda.", "", "", ""), "kosong", None))
        rows.append((("", "", f"TOTAL {self.nama.upper()}", "", r(td, "0"), r(tk_, "0")), "jumlah", "total"))
        self.tb.isi(rows)
        warnai(self.st, td == tk_, "✔ Debit = Kredit", "✖ Debit dan kredit belum seimbang")

    @aman
    def hapus(self):
        sel = self.tb.terpilih()
        if not sel or not sel.startswith("j"):
            raise ValueError("Pilih dulu salah satu baris jurnal yang ingin dihapus.")
        jid = int(sel[1:].split("_")[0])
        if messagebox.askyesno("Hapus jurnal", "Hapus jurnal ini beserta seluruh barisnya?"):
            ly.hapus_jurnal(jid)
            self.segarkan()


class JurnalPenyesuaianDaftar(JurnalDaftar):
    judul = "Jurnal Penyesuaian"
    jenis, nama = "AJP", "Jurnal Penyesuaian"


class InputJurnal(Halaman):
    judul = "Input Jurnal Umum"
    kembali = True
    jenis, prefix, nama = "JU", "JU", "Jurnal Umum"
    cepat = []

    def bangun(self):
        self.opsi, self.baris = [], []
        k = kartu(self.badan)
        k.pack(fill="both", expand=True)
        self.v_tgl, self.v_bukti, self.v_ket = tk.StringVar(value=ly.tgl_input()), tk.StringVar(), tk.StringVar()
        atas = tk.Frame(k, bg=C["kertas"])
        atas.pack(fill="x")
        for c, (teks, var, lebar) in enumerate((("Tanggal (HH-BB-TTTT)", self.v_tgl, 16), ("No. bukti (kosong = otomatis)", self.v_bukti, 24), ("Keterangan", self.v_ket, 60))):
            label(atas, teks, FB).grid(row=0, column=c, sticky="w", padx=(0, 10))
            isian(atas, var, lebar).grid(row=1, column=c, sticky="w", padx=(0, 10), ipady=3)
        if self.cepat:
            cp = tk.Frame(k, bg=C["kertas"])
            cp.pack(fill="x", pady=(10, 0))
            label(cp, "Isi cepat:", F, C["tanah"]).pack(side="left")
            for teks, ket, d, kr in self.cepat:
                tombol(cp, teks, lambda ket=ket, d=d, kr=kr: self._isi_cepat(ket, d, kr), "kedua").pack(side="left", padx=6)
        kepala_kolom(k, (("Akun", 50, "w"), ("Debit", 18, "e"), ("Kredit", 18, "e"))).pack(fill="x", pady=(14, 0))
        self.area = tk.Frame(k, bg=C["kertas"])
        self.area.pack(fill="x")
        pie = tk.Frame(k, bg=C["lime"], padx=10, pady=8)
        pie.pack(fill="x", pady=(6, 0))
        self.j_d, self.j_k = tk.Label(pie, font=FB, bg=C["lime"], fg=C["daun"]), tk.Label(pie, font=FB, bg=C["lime"], fg=C["daun"])
        self.j_d.pack(side="left", padx=(0, 24))
        self.j_k.pack(side="left", padx=(0, 24))
        self.j_s = tk.Label(pie, font=FB, bg=C["lime"])
        self.j_s.pack(side="left")
        aksi = tk.Frame(k, bg=C["kertas"])
        aksi.pack(fill="x", pady=(12, 0))
        tombol(aksi, "+ Tambah baris", lambda: self._tambah_baris(), "kedua").pack(side="left")
        tombol(aksi, "Simpan", self.simpan).pack(side="right")
        self._reset()

    def _cari(self, kode):
        return next((o for o in self.opsi if o.startswith(kode + " ")), "")

    def _tambah_baris(self):
        f = tk.Frame(self.area, bg=C["kertas"])
        f.pack(fill="x", pady=2)
        va, vd, vk = tk.StringVar(), tk.StringVar(), tk.StringVar()
        cb = pilihan(f, va, self.opsi, 52)
        cb.pack(side="left", padx=(0, 6))
        isian(f, vd, 18, justify="right").pack(side="left", padx=(0, 6), ipady=3)
        isian(f, vk, 18, justify="right").pack(side="left", padx=(0, 6), ipady=3)
        b = dict(f=f, akun=va, d=vd, k=vk, cb=cb)
        tk.Button(f, text="x", fg=C["merah"], bg=C["kertas"], relief="flat", bd=0, cursor="hand2", font=FB,
                  command=lambda: self._hapus_baris(b)).pack(side="left")
        vd.trace_add("write", lambda *_: self._ubah(b, "d"))
        vk.trace_add("write", lambda *_: self._ubah(b, "k"))
        self.baris.append(b)

    def _hapus_baris(self, b):
        if len(self.baris) > 2:
            b["f"].destroy()
            self.baris.remove(b)
            self._hitung()

    def _ubah(self, b, sisi):
        lain = "k" if sisi == "d" else "d"
        if b[sisi].get().strip():       # satu baris hanya debit ATAU kredit
            b[lain].set("")
        self._hitung()

    def _hitung(self):
        d = k = ly.Z
        for b in self.baris:
            try:
                d += ly.angka(b["d"].get())
                k += ly.angka(b["k"].get())
            except ValueError:
                pass
        self.j_d.config(text="Total debit: " + ly.rp(d, "0"))
        self.j_k.config(text="Total kredit: " + ly.rp(k, "0"))
        if d == 0 and k == 0:
            self.j_s.config(text="")
        else:
            warnai(self.j_s, d == k, "✔ Seimbang", "✖ Selisih " + ly.rp(abs(d - k)))

    def _reset(self):
        for b in self.baris:
            b["f"].destroy()
        self.baris = []
        self.v_bukti.set("")
        self.v_ket.set("")
        self._tambah_baris()
        self._tambah_baris()
        self._hitung()

    def _isi_cepat(self, ket, d, kr):
        self._reset()
        self.v_ket.set(ket)
        self.baris[0]["akun"].set(self._cari(d))
        self.baris[1]["akun"].set(self._cari(kr))

    @aman
    def simpan(self):
        baris = [(b["akun"].get().split()[0] if b["akun"].get() else "", b["d"].get(), b["k"].get()) for b in self.baris]
        ly.simpan_jurnal(self.jenis, self.prefix, self.v_tgl.get(), self.v_bukti.get(), self.v_ket.get(), baris)
        messagebox.showinfo("Tersimpan", f"{self.nama} tersimpan dan sudah diposting ke buku besar.")
        self._reset()
        return True

    @aman
    def segarkan(self):
        self.opsi = [f"{a['kode']}  {a['nama']}" for a in ly.daftar_akun() if a["kode"] != "3-103"]
        for b in self.baris:
            b["cb"]["values"] = self.opsi


class InputJurnalPenyesuaian(InputJurnal):
    judul = "Input Jurnal Penyesuaian"
    jenis, prefix, nama = "AJP", "AJP", "Jurnal Penyesuaian"
    cepat = [("Penyusutan peralatan", "Penyusutan peralatan periode ini", "7-105", "1-108"),
             ("Gaji terutang", "Gaji pekerja yang masih terutang", "7-101", "2-102")]


# =================================================================== PERSEDIAAN: kartu stok (siklus) dan input (beranda)
class Persediaan(Halaman):
    judul = "Persediaan"

    def bangun(self):
        self.tabel, self.stat, self.peta = {}, {}, {}
        for kode in psd.STOK:
            bar = tk.Frame(self.badan, bg=C["krim"])
            bar.pack(fill="x", pady=(8, 2))
            label(bar, f"Kartu stok {psd.STOK[kode]} ({kode})", FH2, bg=C["krim"]).pack(side="left")
            self.stat[kode] = tk.Label(bar, font=("Segoe UI", 9, "bold"), bg=C["krim"])
            self.stat[kode].pack(side="right")
            tb = Tabel(self.badan, [("Tanggal", 100, "w"), ("Keterangan", 300, "w"), ("Mutasi", 70, "w"), ("Jumlah kg", 90, "e"),
                                    ("Harga/kg", 100, "e"), ("Nilai (Rp)", 120, "e"), ("Saldo kg", 90, "e"), ("Saldo Rp", 130, "e")], tinggi=7)
            tb.pack(fill="both", expand=True)
            self.tabel[kode] = tb
        tombol(self.badan, "Hapus transaksi terakhir yang dipilih", self.hapus, "bahaya").pack(anchor="w", pady=(10, 0))

    @aman
    def segarkan(self):
        net = ak.muat().net(("JU",))
        self.peta = {}
        for kode in psd.STOK:
            ks = psd.kartu_stok(kode)
            rows = []
            for n, x in enumerate(ks["rows"]):
                iid = f"{kode}|{n}"
                self.peta[iid] = (x["jid"], x["terakhir"])
                rows.append(((ly.tgl(x["tgl"]), x["ket"] or "", x["jenis"].capitalize(), ly.kg(x["qty"]), r(x["harga"], "0"),
                              r(x["total"], "0"), ly.kg(x["sq"]), r(x["sn"], "0")), None, iid))
            if not rows:
                rows.append((("", "Belum ada mutasi.", "", "", "", "", "", ""), "kosong", None))
            rows.append((("", "Saldo kartu stok", "", "", "", "", ly.kg(ks["qty"]), r(ks["nilai"], "0")), "jumlah", None))
            self.tabel[kode].isi(rows)
            sama = ks["nilai"] == net[kode]
            warnai(self.stat[kode], sama, f"✔ Sama dengan saldo akun {kode} di buku besar",
                   f"✖ Saldo buku besar {kode} Rp {ly.rp(net[kode], '0')}, beda dari kartu stok (mungkin ada jurnal manual)")

    @aman
    def hapus(self):
        for tb in self.tabel.values():
            sel = tb.terpilih()
            if sel in self.peta:
                jid, _ = self.peta[sel]
                if not jid:
                    raise ValueError("Persediaan awal diubah lewat Input Saldo Awal di Beranda.")
                if messagebox.askyesno("Hapus transaksi", "Hapus transaksi persediaan ini beserta jurnalnya?"):
                    psd.hapus(jid)
                    self.segarkan()
                return
        raise ValueError("Pilih dulu baris transaksi yang ingin dihapus pada kartu stok.")


class InputPersediaan(Halaman):
    judul = "Input Persediaan"
    kembali = True

    def bangun(self):
        self.badan.columnconfigure((0, 1, 2), weight=1, uniform="f")
        self._form(0, "Beli dari petani", [("tgl", "Tanggal (HH-BB-TTTT)", "tgl", None), ("qty", "Jumlah (kg)", "num", None),
                   ("harga", "Harga beli per kg (Rp)", "num", None), ("akun", "Dibayar", "pilih", psd.PEMBAYARAN), ("ket", "Keterangan", "teks", None)],
                   "Simpan pembelian", lambda d: psd.pembelian(ly.tanggal(d["tgl"]), ly.angka(d["qty"], False), ly.angka(d["harga"]), d["akun"], d["ket"].strip()))
        self._form(1, "Jual alpukat", [("tgl", "Tanggal (HH-BB-TTTT)", "tgl", None), ("produk", "Produk", "pilih", {k: p["nama"] for k, p in psd.PRODUK.items()}),
                   ("qty", "Jumlah (kg)", "num", None), ("harga", "Harga jual per kg (Rp)", "num", None),
                   ("akun", "Diterima", "pilih", psd.PENERIMAAN), ("ket", "Keterangan", "teks", None)],
                   "Simpan penjualan", lambda d: psd.penjualan(ly.tanggal(d["tgl"]), d["produk"], ly.angka(d["qty"], False), ly.angka(d["harga"]), d["akun"], d["ket"].strip()))
        self._form(2, "Olah jadi frozen", [("tgl", "Tanggal (HH-BB-TTTT)", "tgl", None), ("qs", "Segar diolah (kg)", "num", None),
                   ("qf", "Hasil frozen (kg)", "num", None), ("ket", "Keterangan", "teks", None)],
                   "Simpan produksi", lambda d: psd.produksi_frozen(ly.tanggal(d["tgl"]), ly.angka(d["qs"], False), ly.angka(d["qf"], False), d["ket"].strip()))

    def _form(self, kol, judul, fields, teks_btn, aksi):
        k = kartu(self.badan)
        k.grid(row=0, column=kol, sticky="new", padx=6)
        label(k, judul, FH2).pack(anchor="w")
        entri = {}
        for key, teks, jenis, opsi in fields:
            label(k, teks, FB).pack(anchor="w", pady=(8, 2))
            v = tk.StringVar()
            if jenis == "pilih":
                cb = pilihan(k, v, list(opsi.values()), 30)
                cb.current(0)
                cb.pack(fill="x")
            else:
                if jenis == "tgl":
                    v.set(ly.tgl_input())
                isian(k, v, 30).pack(fill="x", ipady=3)
            entri[key] = (v, jenis, opsi)

        @aman
        def kirim():
            data = {}
            for key, (v, jenis, opsi) in entri.items():
                nilai = v.get()
                data[key] = next(kd for kd, lb in opsi.items() if lb == nilai) if jenis == "pilih" else nilai
            aksi(data)
            messagebox.showinfo("Tersimpan", "Transaksi persediaan tersimpan dan jurnal umum dibuat otomatis.")
            for v, jenis, _ in entri.values():
                if jenis in ("num", "teks"):
                    v.set("")
        tombol(k, teks_btn, kirim).pack(anchor="w", pady=(14, 0))


# =================================================================== LAPORAN-LAPORAN
class BukuBesar(Halaman):
    judul = "Buku Besar"
    jenis = ("JU",)

    def bangun(self):
        self.tb = Tabel(self.badan, [("Tanggal", 105, "w"), ("Keterangan", 430, "w"), ("Bukti", 90, "w"),
                                     ("Debit", 140, "e"), ("Kredit", 140, "e"), ("Saldo", 160, "e")], tinggi=24)
        self.tb.pack(fill="both", expand=True)

    @aman
    def segarkan(self):
        rows = []
        for g in ak.muat().buku_besar(self.jenis):
            rows.append((("", f"{g['kode']}   {g['nama']}", "", "", "", f"saldo normal {'debit' if g['normal'] == 'D' else 'kredit'}"), "judul", None))
            for x in g["baris"]:
                ajp = x["jenis"] == "AJP"
                rows.append(((ly.tgl(x["tgl"]), (x["ket"] or "") + ("   [penyesuaian]" if ajp else ""), x["bukti"] or "",
                              r(x["d"]), r(x["k"]), r(x["saldo"], "0")), "ajp" if ajp else None, None))
            rows.append((("", f"Jumlah {g['nama']}", "", r(g["td"], "0"), r(g["tk"], "0"), r(g["saldo"], "0")), "jumlah", None))
        if not rows:
            rows = [(("", "Belum ada data.", "", "", "", ""), "kosong", None)]
        self.tb.isi(rows)


class BukuBesarAjp(BukuBesar):
    judul = "Buku Besar Setelah Penyesuaian"
    jenis = ("JU", "AJP")


class NeracaSaldo(Halaman):
    judul = "Neraca Saldo"
    akhir = False

    def bangun(self):
        self.tb = Tabel(self.badan, [("Kode", 90, "w"), ("Nama Akun", 420, "w"), ("Debit", 180, "e"), ("Kredit", 180, "e")], tinggi=20)
        self.tb.pack(fill="both", expand=True)
        self.st = tk.Label(self.badan, font=FB, bg=C["krim"])
        self.st.pack(anchor="w", pady=(8, 0))

    @aman
    def segarkan(self):
        b = ak.muat()
        rows, td, tk_ = b.saldo_akhir() if self.akhir else b.neraca_saldo()
        data = [((x["kode"], x["nama"], r(x["d"]), r(x["k"])), None, None) for x in rows]
        if not data:
            data = [(("", "Belum ada data.", "", ""), "kosong", None)]
        data.append((("", "TOTAL", r(td, "0"), r(tk_, "0")), "jumlah", None))
        self.tb.isi(data)
        warnai(self.st, td == tk_, "✔ Seimbang", f"✖ Tidak seimbang, selisih Rp {ly.rp(td - tk_)}")


class NeracaSaldoAkhir(NeracaSaldo):
    judul = "Neraca Saldo Akhir"
    akhir = True


class NeracaLajur(Halaman):
    judul = "Neraca Lajur"
    KS = ["ns_d", "ns_k", "aj_d", "aj_k", "na_d", "na_k", "lr_d", "lr_k", "nr_d", "nr_k"]

    def bangun(self):
        nama = ["NS Debit", "NS Kredit", "Penyesuaian D", "Penyesuaian K", "Disesuaikan D", "Disesuaikan K",
                "Laba Rugi D", "Laba Rugi K", "Neraca D", "Neraca K"]
        self.tb = Tabel(self.badan, [("Kode", 70, "w"), ("Nama Akun", 250, "w")] + [(n, 112, "e") for n in nama], tinggi=24)
        self.tb.pack(fill="both", expand=True)

    @aman
    def segarkan(self):
        nl = ak.muat().neraca_lajur()
        rows = [((x["kode"], x["nama"]) + tuple(r(x[k]) for k in self.KS), None, None) for x in nl["rows"]]
        if not rows:
            rows = [(("", "Belum ada data.") + ("",) * 10, "kosong", None)]
        rows.append((("", "JUMLAH") + tuple(r(nl["tot"][k], "0") for k in self.KS), "jumlah", None))
        rows.append((("", f"SELISIH {nl['status'].upper()} BERSIH Rp {ly.rp(nl['besar'], '0')}") + tuple(r(nl["sel"][k]) for k in self.KS),
                     "rugi" if nl["status"] == "Rugi" else "selisih", None))
        rows.append((("", "JUMLAH SEIMBANG") + tuple(r(nl["akhir"][k], "0") for k in self.KS), "akhir", None))
        self.tb.isi(rows)


class Laporan(Halaman):
    judul = "Laporan Keuangan"

    def bangun(self):
        nb = ttk.Notebook(self.badan)
        nb.pack(fill="both", expand=True)
        self.tabel = {}
        for kunci, teks in (("lr", "📈  Laba Rugi"), ("ek", "⚖  Perubahan Ekuitas"), ("pos", "🏦  Posisi Keuangan")):
            f = tk.Frame(nb, bg=C["krim"], pady=10)
            nb.add(f, text=teks)
            self.tabel[kunci] = Tabel(f, [("Keterangan", 520, "w"), ("Rincian", 170, "e"), ("Jumlah", 170, "e")], tinggi=22)
            self.tabel[kunci].pack(fill="both", expand=True)
        self.st = tk.Label(self.badan, font=FB, bg=C["krim"])
        self.st.pack(anchor="w", pady=(8, 0))

    @aman
    def segarkan(self):
        pg = ly.pengaturan()
        lap = ak.muat().laporan()
        lr, ek, pos = lap["lr"], lap["ek"], lap["pos"]
        rj = lambda v: ly.rp(v)
        ind = "      "

        a = [(("Pendapatan", "", ""), "sub", None)]
        a += [((ind + x["nama"], rj(x["jml"]), ""), None, None) for x in lr["pend"]]
        a += [((ind + "(-) " + x["nama"], f"({rj(x['jml'])})", ""), None, None) for x in lr["poto"]]
        a.append((("Penjualan Bersih", "", ly.rp(lr["penjualan_bersih"], "0")), "jumlah", None))
        a.append((("Harga Pokok Penjualan", "", ""), "sub", None))
        a += [((ind + ("(-) " if x["normal"] == "K" else "") + x["nama"], rj(x["jml"]), ""), None, None) for x in lr["beli"]]
        a += [((ind + x["nama"], rj(x["jml"]), ""), None, None) for x in lr["hpp"]]
        a.append((("Total Harga Pokok Penjualan", "", ly.rp(lr["total_hpp"], "0")), "jumlah", None))
        a.append((("LABA KOTOR", "", ly.rp(lr["laba_kotor"], "0")), "hasil", None))
        a.append((("Beban Operasional", "", ""), "sub", None))
        a += [((ind + x["nama"], rj(x["jml"]), ""), None, None) for x in lr["beban"]]
        a.append((("Total Beban Operasional", "", ly.rp(lr["total_beban"], "0")), "jumlah", None))
        a.append((("LABA USAHA", "", ly.rp(lr["laba_usaha"], "0")), "hasil", None))
        a += [((x["nama"], "", rj(x["jml"])), None, None) for x in lr["lain"]]
        a.append(((("LABA" if lr["laba"] >= 0 else "RUGI") + " BERSIH", "", ly.rp(lr["laba"], "0")), "total", None))
        self.tabel["lr"].isi(a)

        e = [(("Modal Pemilik, awal periode", "", ly.rp(ek["modal_awal"], "0")), None, None),
             ((ind + "Penambahan modal", "", ly.rp(ek["tambahan"], "0")), None, None),
             ((ind + ("Laba" if ek["laba"] >= 0 else "Rugi") + " bersih periode berjalan", "", ly.rp(ek["laba"], "0")), None, None),
             ((ind + "Prive", "", f"({ly.rp(ek['prive'], '0')})"), None, None),
             (("MODAL PEMILIK, AKHIR PERIODE", "", ly.rp(ek["modal_akhir"], "0")), "total", None)]
        self.tabel["ek"].isi(e)

        p = [(("ASET", "", ""), "sub", None), (("Aset Lancar", "", ""), "kepala", None)]
        p += [((ind + x["nama"], rj(x["jml"]), ""), None, None) for x in pos["lancar"]]
        p.append((("Total Aset Lancar", "", ly.rp(pos["total_lancar"], "0")), "jumlah", None))
        p.append((("Aset Tetap", "", ""), "kepala", None))
        p += [((ind + x["nama"], rj(x["jml"]), ""), None, None) for x in pos["tetap"]]
        p.append((("Total Aset Tetap", "", ly.rp(pos["total_tetap"], "0")), "jumlah", None))
        p.append((("TOTAL ASET", "", ly.rp(pos["total_aset"], "0")), "total", None))
        p.append((("LIABILITAS", "", ""), "sub", None))
        p += [((ind + x["nama"], rj(x["jml"]), ""), None, None) for x in pos["liab"]]
        p.append((("Total Liabilitas", "", ly.rp(pos["total_liab"], "0")), "jumlah", None))
        p.append((("EKUITAS", "", ""), "sub", None))
        p.append(((ind + "Modal Pemilik", ly.rp(pos["modal_akhir"], "0"), ""), None, None))
        p.append((("TOTAL LIABILITAS + EKUITAS", "", ly.rp(pos["total_pasiva"], "0")), "total", None))
        self.tabel["pos"].isi(p)
        warnai(self.st, pos["seimbang"], f"✔ Aset = Liabilitas + Ekuitas      {pg['nama_usaha']}, {pg['nama_periode']}",
               "✖ Neraca belum seimbang, periksa saldo awal dan jurnal")


class Penutup(Halaman):
    judul = "Jurnal Penutup"

    def bangun(self):
        bar = tk.Frame(self.badan, bg=C["krim"])
        bar.pack(fill="x", pady=(0, 8))
        tombol(bar, "Simpan jurnal penutup ke database", self.simpan).pack(side="left")
        self.st = tk.Label(bar, font=FB, bg=C["krim"])
        self.st.pack(side="right")
        self.tb = Tabel(self.badan, [("Tanggal", 105, "w"), ("Keterangan / Akun", 520, "w"), ("Ref", 80, "w"),
                                     ("Debit", 150, "e"), ("Kredit", 150, "e")], tinggi=22)
        self.tb.pack(fill="both", expand=True)

    @aman
    def segarkan(self):
        ent, td, tk_ = ak.muat().penutup()
        rows = []
        for e in ent:
            rows.append(((ly.tgl(e["tanggal"]), f"{e['no']}. {e['ket']}", "", "", ""), "kepala", None))
            for x in e["baris"]:
                rows.append((("", ("      " if x["k"] else "") + x["nama"], x["kode"], r(x["d"]), r(x["k"])), None, None))
        if not rows:
            rows = [(("", "Belum ada akun sementara yang bersaldo.", "", "", ""), "kosong", None)]
        rows.append((("", "TOTAL JURNAL PENUTUP", "", r(td, "0"), r(tk_, "0")), "jumlah", None))
        self.tb.isi(rows)
        warnai(self.st, td == tk_, "✔ Seimbang", "✖ Tidak seimbang")

    @aman
    def simpan(self):
        if messagebox.askyesno("Simpan jurnal penutup", "Simpan jurnal penutup ke database? Data jurnal penutup lama akan diganti."):
            n = ly.simpan_penutup(ak.muat())
            messagebox.showinfo("Tersimpan", f"{n} jurnal penutup tersimpan di database.")


# =================================================================== APLIKASI
MENU = [
    ("Persiapan", [("beranda", "Beranda", "", Beranda), ("akun", "Daftar Akun", "", DaftarAkun), ("saldo_awal", "Saldo Awal", "0", SaldoAwalLihat)]),
    ("Siklus Akuntansi", [("ju", "Jurnal Umum", "1", JurnalDaftar), ("persediaan", "Persediaan", "", Persediaan),
                          ("bb", "Buku Besar", "2", BukuBesar), ("ns", "Neraca Saldo", "3", NeracaSaldo),
                          ("ajp", "Jurnal Penyesuaian", "4", JurnalPenyesuaianDaftar), ("bb_ajp", "Buku Besar Setelah Penyesuaian", "5", BukuBesarAjp),
                          ("nl", "Neraca Lajur", "6", NeracaLajur), ("lap", "Laporan Keuangan", "7", Laporan),
                          ("pnt", "Jurnal Penutup", "8", Penutup), ("nsa", "Neraca Saldo Akhir", "9", NeracaSaldoAkhir)]),
]
HALAMAN_INPUT = {"in_saldo": InputSaldoAwal, "in_ju": InputJurnal, "in_ajp": InputJurnalPenyesuaian, "in_psd": InputPersediaan}


class Aplikasi(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ambarawa Avocado")
        self.geometry("1360x780")
        self.minsize(1100, 660)
        self.configure(bg=C["krim"])
        gaya(self)
        self.sisi = tk.Frame(self, bg=C["daun"], width=260)
        self.sisi.pack(side="left", fill="y")
        self.sisi.pack_propagate(False)
        self.isi = tk.Frame(self, bg=C["krim"])
        self.isi.pack(side="right", fill="both", expand=True)
        self.kelas, self.halaman, self.item, self.aktif = dict(HALAMAN_INPUT), {}, {}, None
        self._sisi()
        self.show("beranda")

    def _sisi(self):
        merek = tk.Frame(self.sisi, bg=C["daun"])
        merek.pack(fill="x", padx=18, pady=(22, 8))
        kv = tk.Canvas(merek, width=36, height=50, bg=C["daun"], highlightthickness=0)
        kv.create_oval(10, 2, 26, 24, fill="#ffffff", outline="")
        kv.create_oval(3, 12, 33, 48, fill="#ffffff", outline="")
        kv.create_oval(13, 28, 23, 40, fill=C["daun"], outline="")
        kv.pack(side="left")
        tb = tk.Frame(merek, bg=C["daun"])
        tb.pack(side="left", padx=10)
        tk.Label(tb, text="Ambarawa", font=("Segoe UI", 16, "bold"), fg="#ffffff", bg=C["daun"]).pack(anchor="w")
        tk.Label(tb, text="AVOCADO", font=("Segoe UI", 9), fg="#cfe3d3", bg=C["daun"]).pack(anchor="w")
        for judul, items in MENU:
            tk.Label(self.sisi, text=judul.upper(), font=("Segoe UI", 8, "bold"), fg="#cfe3d3", bg=C["daun"]).pack(anchor="w", padx=22, pady=(16, 4))
            for kunci, teks, no, kelas in items:
                self.kelas[kunci] = kelas
                f = tk.Frame(self.sisi, bg=C["daun"], cursor="hand2")
                f.pack(fill="x", padx=12, pady=1)
                n = tk.Label(f, text=no, width=2, font=("Segoe UI", 9, "bold"), fg="#cfe3d3", bg=C["daun"])
                n.pack(side="left", padx=(8, 6), pady=6)
                t = tk.Label(f, text=teks, font=F, fg="#ffffff", bg=C["daun"], anchor="w")
                t.pack(side="left", fill="x", expand=True)
                for w in (f, n, t):
                    w.bind("<Button-1>", lambda e, k=kunci: self.show(k))
                self.item[kunci] = (f, n, t)
        tk.Frame(self.sisi, bg=C["daun"]).pack(fill="both", expand=True)
        tombol(self.sisi, "Unduh semua (Excel)", self.unduh, "putih").pack(fill="x", padx=18, pady=(0, 18))

    def _sorot(self, kunci, aktif):
        f, n, t = self.item[kunci if kunci in self.item else "beranda"]
        if aktif:
            f.config(bg="#ffffff"), n.config(bg="#ffffff", fg=C["daun"]), t.config(bg="#ffffff", fg=C["daun"], font=FB)
        else:
            f.config(bg=C["daun"]), n.config(bg=C["daun"], fg="#cfe3d3"), t.config(bg=C["daun"], fg="#ffffff", font=F)

    def show(self, kunci):
        if self.aktif:
            self.halaman[self.aktif].pack_forget()
            self._sorot(self.aktif, False)
        if kunci not in self.halaman:
            self.halaman[kunci] = self.kelas[kunci](self)
        self.aktif = kunci
        self._sorot(kunci, True)
        self.halaman[kunci].pack(fill="both", expand=True)
        self.halaman[kunci].segarkan()

    @aman
    def unduh(self):
        berkas = export.buat_excel(ak.muat())
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="Siklus_Akuntansi_Ambarawa_Avocado.xlsx",
                                            filetypes=[("Excel", "*.xlsx")])
        if path:
            with open(path, "wb") as fh:
                fh.write(berkas.getvalue())
            messagebox.showinfo("Selesai", f"Laporan diekspor ke:\n{path}")


def main():
    try:
        db.siapkan_database()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Tidak bisa terhubung ke MySQL",
                             f"{e}\n\nPeriksa user/password di config.py dan pastikan MySQL sudah menyala.")
        return
    Aplikasi().mainloop()


if __name__ == "__main__":
    main()
