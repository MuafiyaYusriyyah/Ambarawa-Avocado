"""Tema 'kebun alpukat' dan komponen visual (tkinter murni)."""
import functools
import tkinter as tk
from tkinter import messagebox, ttk

C = dict(daun="#2f5d3a", daun2="#3f7a4e", alpukat="#cfe3d3", lime="#e9efe9", krim="#f5f6f3", kertas="#ffffff",
         biji="#2b2f2a", tanah="#6b726b", garis="#d9ddd6", merah="#b3402c", teks="#262b25", hijau_ok="#2f5d3a")
F = ("Segoe UI", 10)
FB = ("Segoe UI", 10, "bold")
FJ = ("Segoe UI", 20, "bold")
FH2 = ("Segoe UI", 12, "bold")


def aman(fungsi):
    """Tangkap galat: ValueError = salah input (peringatan), lainnya = kendala database/program."""
    @functools.wraps(fungsi)
    def bungkus(*a, **k):
        try:
            return fungsi(*a, **k)
        except ValueError as e:
            messagebox.showwarning("Periksa kembali", str(e))
        except Exception as e:
            messagebox.showerror("Terjadi kendala", f"{e}\n\nPeriksa koneksi MySQL di config.py dan pastikan MySQL menyala.")
    return bungkus


def gaya(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure("Treeview", background=C["kertas"], fieldbackground=C["kertas"], foreground=C["teks"],
                rowheight=27, font=F, bordercolor=C["garis"], borderwidth=1)
    s.configure("Treeview.Heading", background=C["daun"], foreground="#ffffff", font=FB, relief="flat", padding=(6, 7))
    s.map("Treeview.Heading", background=[("active", C["daun2"])])
    s.map("Treeview", background=[("selected", C["alpukat"])], foreground=[("selected", C["daun"])])
    s.configure("TNotebook", background=C["krim"], borderwidth=0)
    s.configure("TNotebook.Tab", padding=(18, 8), font=FB, background=C["lime"], foreground=C["daun"], borderwidth=0)
    s.map("TNotebook.Tab", background=[("selected", C["daun"])], foreground=[("selected", "#ffffff")])
    s.configure("TCombobox", fieldbackground="#ffffff", padding=4)
    s.configure("Vertical.TScrollbar", background=C["lime"], troughcolor=C["krim"])
    s.configure("Horizontal.TScrollbar", background=C["lime"], troughcolor=C["krim"])
    root.option_add("*TCombobox*Listbox.font", F)


def tombol(induk, teks, perintah, jenis="utama"):
    bg, fg = {"utama": (C["daun"], "#ffffff"), "kedua": (C["lime"], C["daun"]), "bahaya": ("#f6e0dc", C["merah"]),
              "putih": ("#ffffff", C["daun"])}[jenis]
    return tk.Button(induk, text=teks, command=perintah, bg=bg, fg=fg, activebackground=C["daun2"],
                     activeforeground="#ffffff", relief="flat", bd=0, font=FB, padx=14, pady=7, cursor="hand2")


def kartu(induk, **kw):
    return tk.Frame(induk, bg=C["kertas"], highlightbackground=C["garis"], highlightthickness=1,
                    padx=kw.pop("padx", 16), pady=kw.pop("pady", 14), **kw)


def label(induk, teks, font=F, fg=None, bg=None, **kw):
    return tk.Label(induk, text=teks, font=font, fg=fg or C["biji"], bg=bg or induk["bg"], **kw)


def isian(induk, var=None, lebar=18, **kw):
    return tk.Entry(induk, textvariable=var, width=lebar, font=F, relief="flat", bg="#ffffff", fg=C["teks"],
                    highlightthickness=1, highlightbackground=C["garis"], highlightcolor=C["daun2"],
                    insertbackground=C["daun"], **kw)


def pilihan(induk, var, nilai, lebar=24):
    cb = ttk.Combobox(induk, textvariable=var, values=nilai, state="readonly", width=lebar, font=F)
    return cb


class Tabel(tk.Frame):
    """Treeview bergaya, dengan baris khusus (judul, jumlah, total, dll.)."""

    def __init__(self, induk, kolom, tinggi=12):
        super().__init__(induk, bg=C["kertas"], highlightbackground=C["garis"], highlightthickness=1)
        self.tv = ttk.Treeview(self, columns=[str(i) for i in range(len(kolom))], show="headings", height=tinggi)
        for i, (judul, lebar, rata) in enumerate(kolom):
            self.tv.heading(str(i), text=judul, anchor="e" if rata == "e" else "w")
            self.tv.column(str(i), width=lebar, minwidth=60, anchor=rata, stretch=(rata != "e"))
        vs = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        hs = ttk.Scrollbar(self, orient="horizontal", command=self.tv.xview)
        self.tv.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.tv.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        tebal = ("Segoe UI", 10, "bold")
        t = self.tv.tag_configure
        t("genap", background="#f7f8f5")
        t("kepala", background=C["lime"], font=tebal)
        t("judul", background=C["daun2"], foreground="#ffffff", font=tebal)
        t("jumlah", background=C["lime"], font=tebal)
        t("hasil", background=C["lime"], font=tebal)
        t("selisih", background=C["alpukat"], font=tebal)
        t("rugi", background="#f6e0dc", font=tebal)
        t("akhir", background=C["alpukat"], foreground=C["daun"], font=tebal)
        t("total", background=C["daun"], foreground="#ffffff", font=tebal)
        t("sub", background=C["krim"], foreground=C["daun"], font=tebal)
        t("ajp", background="#eef3ee")
        t("kosong", foreground=C["tanah"], font=("Segoe UI", 10, "italic"))

    def isi(self, baris):
        """baris: [(nilai-nilai, tag, iid)], tag dan iid boleh None."""
        self.tv.delete(*self.tv.get_children())
        for n, b in enumerate(baris):
            nilai, tag, iid = (list(b) + [None, None])[:3]
            tags = (tag,) if tag else (("genap",) if n % 2 else ())
            self.tv.insert("", "end", iid=iid, values=nilai, tags=tags)

    def terpilih(self):
        s = self.tv.selection()
        return s[0] if s else None


class GulungFrame(tk.Frame):
    """Area isi yang bisa di-scroll (dipakai halaman Saldo Awal)."""

    def __init__(self, induk):
        super().__init__(induk, bg=C["kertas"])
        self.kanvas = tk.Canvas(self, bg=C["kertas"], highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.kanvas.yview)
        self.isi = tk.Frame(self.kanvas, bg=C["kertas"])
        self.isi.bind("<Configure>", lambda e: self.kanvas.configure(scrollregion=self.kanvas.bbox("all")))
        self.jendela = self.kanvas.create_window((0, 0), window=self.isi, anchor="nw")
        self.kanvas.bind("<Configure>", lambda e: self.kanvas.itemconfigure(self.jendela, width=e.width))
        self.kanvas.configure(yscrollcommand=sb.set)
        self.kanvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        for w in (self.kanvas, self.isi):
            w.bind("<Enter>", self._masuk)
            w.bind("<Leave>", self._keluar)

    def _roda(self, e):
        arah = -1 if (getattr(e, "delta", 0) > 0 or getattr(e, "num", 0) == 4) else 1
        self.kanvas.yview_scroll(arah, "units")

    def _masuk(self, _):
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.kanvas.bind_all(ev, self._roda)

    def _keluar(self, _):
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.kanvas.unbind_all(ev)


class Halaman(tk.Frame):
    """Dasar semua halaman: judul + area isi. kembali=True menambah tombol ke Beranda (halaman input)."""
    judul = ""
    kembali = False

    def __init__(self, app):
        super().__init__(app.isi, bg=C["krim"])
        self.app = app
        kepala = tk.Frame(self, bg=C["krim"])
        kepala.pack(fill="x", padx=26, pady=(20, 4))
        if self.kembali:
            tombol(kepala, "Kembali ke Beranda", lambda: app.show("beranda"), "kedua").pack(side="right", anchor="n")
        tk.Label(kepala, text=self.judul, font=FJ, fg=C["daun"], bg=C["krim"]).pack(anchor="w")
        tk.Frame(self, bg=C["daun"], height=2).pack(fill="x", padx=26, pady=(10, 12))
        self.badan = tk.Frame(self, bg=C["krim"])
        self.badan.pack(fill="both", expand=True, padx=26, pady=(0, 18))
        self.bangun()

    def bangun(self):
        pass

    def segarkan(self):
        pass
