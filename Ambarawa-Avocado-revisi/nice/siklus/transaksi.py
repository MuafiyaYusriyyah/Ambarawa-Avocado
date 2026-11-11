"""INPUT TRANSAKSI - Penerimaan, Pengeluaran, dan Transaksi Lainnya.

Inilah pintu masuk seluruh siklus. Setiap transaksi yang disimpan di sini otomatis menghasilkan:
    jurnal umum (ju.py)  ->  kartu stok bila menyangkut alpukat (persediaan.py)  ->  buku besar  ->  neraca saldo  -> ... -> laporan
sehingga semua input saling nyambung dalam satu siklus tanpa perlu menjurnal dua kali.

Daftar jenis transaksi ada di ITEM di bawah. Menambah jenis baru cukup menambah satu baris `_i(...)`."""
import datetime as dt

import streamlit as st

from core.db import ambil, cursor
from core.util import B, I, Z, angka, dec, kol, rp, tgl as tgl_teks
from siklus import ju, persediaan as psd
from ui.komponen import bagian, jalankan, pesan, pilih_hapus, tampil

# akun tempat uang diterima / dibayar
CARA = {"Tunai": "1-101", "Transfer Bank BRI": "1-102"}
JUAL_P, BELI_P = ("segar", "frozen", "jus"), ("segar", "frozen")
PERALATAN = ("1-106", "1-107")

KELOMPOK = {
    "TERIMA": dict(judul="Penerimaan", label_cara="Diterima ke", prefix="KM",
                   catatan="Catat semua uang yang masuk. Penjualan alpukat otomatis mengurangi stok dan mencatat harga pokok (HPP). "
                           "Setiap transaksi langsung masuk Jurnal Umum, Buku Besar, dan seluruh laporan."),
    "KELUAR": dict(judul="Pengeluaran", label_cara="Dibayar dari", prefix="KK",
                   catatan="Catat semua uang yang keluar. Pembelian alpukat otomatis menambah stok di kartu stok. "
                           "Setiap transaksi langsung masuk Jurnal Umum, Buku Besar, dan seluruh laporan."),
    "LAIN": dict(judul="Transaksi Lainnya", label_cara="", prefix="TL",
                 catatan="Untuk transaksi yang belum melibatkan kas, seperti pembelian atau penjualan secara kredit. "
                         "Nama customer / supplier wajib diisi agar mudah dilacak."),
}


def _i(k, nama, tipe, kelompok, **kw):
    """Satu jenis transaksi.
    tipe  : jual (kg x harga + HPP) | beli (kg x harga) | nominal (satu angka) | olah (segar -> frozen)
    lawan : untuk jual/beli, akun lawan. "CARA" = kas/bank pilihan pengguna, atau kode akun tetap (mis. piutang)
    dr/kr : untuk nominal, akun debit dan kredit. "CARA" = kas/bank pilihan, "PILIH" = akun pilihan dari daftar `pilih`"""
    d = dict(k=k, nama=nama, tipe=tipe, kelompok=kelompok, produk=(), lawan="CARA", dr=None, kr=None, pilih=None,
             wajib_pihak=False, label_pihak="Nama (opsional)", info="")
    d.update(kw)
    return d


ITEM = [
    # ---------------------------------------------------------------- PENERIMAAN
    _i("jual_segar", "Penjualan Alpukat Segar", "jual", "TERIMA", produk=("segar",), label_pihak="Nama customer (opsional)"),
    _i("jual_frozen", "Penjualan Alpukat Frozen", "jual", "TERIMA", produk=("frozen",), label_pihak="Nama customer (opsional)"),
    _i("jual_jus", "Penjualan Alpukat untuk Penjual Jus", "jual", "TERIMA", produk=("jus",), label_pihak="Nama customer (opsional)"),
    _i("terima_piutang", "Penerimaan Piutang dari Customer", "nominal", "TERIMA", dr="CARA", kr="1-103", wajib_pihak=True,
       label_pihak="Nama customer", info="Pelunasan penjualan kredit. Mengurangi Piutang Usaha."),
    _i("setor_modal", "Setoran Modal Pemilik", "nominal", "TERIMA", dr="CARA", kr="3-101", label_pihak="Nama penyetor (opsional)"),
    _i("pend_lain", "Pendapatan Lain-lain", "nominal", "TERIMA", dr="CARA", kr="4-104", label_pihak="Dari siapa (opsional)"),
    # ---------------------------------------------------------------- PENGELUARAN
    _i("beli_segar", "Pembelian Alpukat Segar", "beli", "KELUAR", produk=("segar",), label_pihak="Nama supplier (opsional)"),
    _i("beli_frozen", "Pembelian Alpukat Frozen", "beli", "KELUAR", produk=("frozen",), label_pihak="Nama supplier (opsional)"),
    _i("bayar_gaji", "Bayar Gaji", "nominal", "KELUAR", dr="7-101", kr="CARA", label_pihak="Dibayarkan kepada (opsional)"),
    _i("bayar_utang_gaji", "Bayar Utang Gaji", "nominal", "KELUAR", dr="2-102", kr="CARA", label_pihak="Dibayarkan kepada (opsional)",
       info="Pelunasan gaji yang sebelumnya masih terutang."),
    _i("bayar_listrik", "Bayar Listrik", "nominal", "KELUAR", dr="7-110", kr="CARA", label_pihak="Dibayarkan kepada (opsional)"),
    _i("bayar_air", "Bayar Air", "nominal", "KELUAR", dr="7-109", kr="CARA", label_pihak="Dibayarkan kepada (opsional)"),
    _i("bayar_tanaman", "Bayar Perawatan Tanaman", "nominal", "KELUAR", dr="7-102", kr="CARA", label_pihak="Dibayarkan kepada (opsional)"),
    _i("bayar_kirim", "Bayar Ongkos Pengiriman", "nominal", "KELUAR", dr="7-104", kr="CARA", label_pihak="Dibayarkan kepada (opsional)"),
    _i("bayar_produksi", "Bayar Biaya Produksi Frozen", "nominal", "KELUAR", dr="7-103", kr="CARA", label_pihak="Dibayarkan kepada (opsional)"),
    _i("bayar_perlengkapan", "Bayar Perlengkapan", "nominal", "KELUAR", dr="7-106", kr="CARA", label_pihak="Dibayarkan kepada (opsional)"),
    _i("bayar_rusak", "Kompensasi Kerusakan Barang", "nominal", "KELUAR", dr="7-107", kr="CARA", label_pihak="Dibayarkan kepada (opsional)"),
    _i("bayar_beban", "Bayar Beban Lainnya (pilih akun beban)", "nominal", "KELUAR", dr="PILIH", kr="CARA", pilih="Beban",
       label_pihak="Dibayarkan kepada (opsional)", info="Pilih akun beban sendiri, termasuk akun beban yang Anda tambahkan di Daftar Akun."),
    _i("bayar_utang", "Bayar Utang Usaha (ke Supplier)", "nominal", "KELUAR", dr="2-101", kr="CARA", wajib_pihak=True,
       label_pihak="Nama supplier", info="Pelunasan pembelian kredit. Mengurangi Utang Usaha."),
    _i("beli_alat", "Beli Peralatan (tunai)", "nominal", "KELUAR", dr="PILIH", kr="CARA", pilih=PERALATAN, label_pihak="Nama penjual (opsional)"),
    _i("prive", "Prive (Pengambilan Pribadi Pemilik)", "nominal", "KELUAR", dr="3-102", kr="CARA", label_pihak="Keterangan pengambil (opsional)"),
    # ---------------------------------------------------------------- TRANSAKSI LAINNYA (kredit dan non-kas)
    _i("beli_kredit", "Pembelian Kredit", "beli", "LAIN", produk=BELI_P, lawan="2-101", wajib_pihak=True, label_pihak="Nama supplier",
       info="Barang diterima, belum dibayar. Stok bertambah dan Utang Usaha bertambah."),
    _i("jual_kredit", "Penjualan Kredit", "jual", "LAIN", produk=JUAL_P, lawan="1-103", wajib_pihak=True, label_pihak="Nama customer",
       info="Barang dikirim, belum dibayar. Stok berkurang, HPP tercatat, dan Piutang Usaha bertambah."),
    _i("gaji_terutang", "Gaji Terutang (belum dibayar)", "nominal", "LAIN", dr="7-101", kr="2-102", label_pihak="Nama pekerja (opsional)"),
    _i("beban_terutang", "Beban Terutang (belum dibayar, pilih akun beban)", "nominal", "LAIN", dr="PILIH", kr="2-101", pilih="Beban",
       wajib_pihak=True, label_pihak="Nama penagih / supplier", info="Misalnya tagihan listrik atau air yang belum dibayar. Masuk ke Utang Usaha."),
    _i("beli_alat_kredit", "Pembelian Peralatan Kredit", "nominal", "LAIN", dr="PILIH", kr="2-101", pilih=PERALATAN, wajib_pihak=True,
       label_pihak="Nama supplier"),
    _i("olah_frozen", "Produksi Frozen (olah segar menjadi frozen)", "olah", "LAIN", label_pihak="Penanggung jawab (opsional)",
       info="Memindahkan nilai stok segar ke stok frozen sebesar harga rata-rata."),
]
ITEM_K = {i["k"]: i for i in ITEM}


# ------------------------------------------------------------------ ketersediaan jenis transaksi
# Bila sebuah akun dihapus di Daftar Akun, jenis transaksi yang membutuhkannya otomatis hilang dari daftar.
def _jual_beli(it):
    return it["tipe"] in ("jual", "beli")


def perlu(it, pk=None):
    """Kode akun yang wajib ada agar jenis transaksi ini bisa dipakai."""
    kode = set()
    if it["tipe"] == "jual":
        p = psd.PRODUK[pk]
        kode |= {p["stok"], p["jual"], p["hpp"]}
    elif it["tipe"] == "beli":
        kode.add(psd.BELI[pk]["stok"])
    elif it["tipe"] == "olah":
        kode |= {"1-104", "1-105"}
    for x in (it["dr"], it["kr"]):
        if x and x not in ("CARA", "PILIH"):
            kode.add(x)
    if _jual_beli(it) and it["lawan"] != "CARA":
        kode.add(it["lawan"])
    return kode


def pakai_cara(it):
    return it["lawan"] == "CARA" if _jual_beli(it) else "CARA" in (it["dr"], it["kr"])


def opsi_cara(ada):
    return {n: k for n, k in CARA.items() if k in ada}


def opsi_pilih(it, akun):
    p = it["pilih"]
    return [(a["kode"], a["nama"]) for a in akun if (a["kode"] in p if isinstance(p, tuple) else a["kelompok"] == p)]


def produk_ok(it, ada):
    return [pk for pk in it["produk"] if perlu(it, pk) <= ada]


def tersedia(it, akun):
    ada = {a["kode"] for a in akun}
    if _jual_beli(it):
        if not produk_ok(it, ada):
            return False
    elif not perlu(it) <= ada:
        return False
    if pakai_cara(it) and not opsi_cara(ada):
        return False
    return not (it["pilih"] and not opsi_pilih(it, akun))


def item_terdampak(kode):
    """Nama jenis transaksi yang hilang dari daftar input bila akun `kode` dihapus (dipakai halaman Daftar Akun)."""
    akun = ambil("SELECT kode,nama,kelompok FROM akun")
    sisa = [a for a in akun if a["kode"] != kode]
    return [i["nama"] for i in ITEM if tersedia(i, akun) and not tersedia(i, sisa)]


# ------------------------------------------------------------------ merancang jurnal dari satu transaksi
def rancang(c, it, tgl, pihak, qty, harga, nominal, cara, produk, ket, akun_pilih, hasil):
    """Susun jurnal dan mutasi stok TANPA menyimpan (dipakai untuk pratinjau dan penyimpanan).
    Mengembalikan dict: ket, jurnal [(kode, debit, kredit)], mutasi, total, qty, harga, jenis, cara, prefix."""
    pihak, ket = (pihak or "").strip(), (ket or "").strip()
    if it["wajib_pihak"] and not pihak:
        raise ValueError(f"{it['label_pihak']} wajib diisi.")
    tambahan = (f" - {pihak}" if pihak else "") + (f" ({ket})" if ket else "")
    kel = KELOMPOK[it["kelompok"]]
    out = dict(mutasi=[], qty=Z, harga=Z, jenis="", cara=cara if pakai_cara(it) else "Kredit",
               prefix={"jual": "PJ", "beli": "PB", "olah": "PRD"}.get(it["tipe"], kel["prefix"]))
    if pakai_cara(it) and cara not in CARA:
        raise ValueError("Pilih akun kas / bank terlebih dahulu.")

    if it["tipe"] == "olah":
        qs, qf = angka(qty), angka(hasil)
        if qs <= 0 or qf <= 0:
            raise ValueError("Jumlah segar yang diolah dan hasil frozen harus lebih dari 0.")
        q, n = psd.keadaan(c, "1-104")
        if qs > q:
            raise ValueError(f"Stok segar tidak cukup (tersedia {psd.kgs(q)} kg).")
        biaya = n if qs == q else psd.r2(n * qs / q)
        out.update(ket=f"Produksi frozen {psd.kgs(qs)} kg segar jadi {psd.kgs(qf)} kg frozen{tambahan}", total=biaya, qty=qs,
                   harga=biaya / qs, jenis="Segar menjadi Frozen", jurnal=[("1-105", biaya, Z), ("1-104", Z, biaya)],
                   mutasi=[("1-104", "KELUAR", qs, biaya), ("1-105", "MASUK", qf, biaya)])
        return out

    if _jual_beli(it):
        qty, harga = angka(qty), angka(harga)
        if qty <= 0 or harga <= 0:
            raise ValueError("Jumlah (kg) dan harga per kg harus lebih dari 0.")
        lawan = CARA[cara] if it["lawan"] == "CARA" else it["lawan"]
        total = psd.r2(qty * harga)
        if it["tipe"] == "beli":
            p = psd.BELI[produk]
            jurnal, mutasi = [(p["stok"], total, Z), (lawan, Z, total)], [(p["stok"], "MASUK", qty, total)]
        else:
            p = psd.PRODUK[produk]
            q, n = psd.keadaan(c, p["stok"])
            if qty > q:
                raise ValueError(f"Stok {p['nama']} tidak cukup (tersedia {psd.kgs(q)} kg).")
            hpp = n if qty == q else psd.r2(n * qty / q)
            jurnal = [(lawan, total, Z), (p["jual"], Z, total), (p["hpp"], hpp, Z), (p["stok"], Z, hpp)]
            mutasi = [(p["stok"], "KELUAR", qty, hpp)]
        judul = it["nama"] if len(it["produk"]) == 1 else f"{it['nama']} {p['nama']}"
        out.update(ket=f"{judul} {psd.kgs(qty)} kg{tambahan}", total=total, qty=qty, harga=harga, jenis=p["nama"], jurnal=jurnal, mutasi=mutasi)
        return out

    nominal = angka(nominal)
    if nominal <= 0:
        raise ValueError("Nominal harus lebih dari 0.")

    def akun(x):
        if x == "CARA":
            return CARA[cara]
        if x == "PILIH":
            if not akun_pilih:
                raise ValueError("Pilih akunnya terlebih dahulu.")
            return akun_pilih
        return x
    out.update(ket=f"{it['nama']}{tambahan}", total=nominal, jurnal=[(akun(it["dr"]), nominal, Z), (akun(it["kr"]), Z, nominal)])
    return out


# ------------------------------------------------------------------ simpan dan hapus
def simpan(key, tgl, pihak, qty, harga, nominal, cara, produk, ket, akun_pilih, hasil, bukti):
    """Simpan transaksi + jurnal umum + mutasi stok dalam satu transaksi database. Mengembalikan nomor bukti."""
    it = ITEM_K[key]
    with cursor(True) as c:
        r = rancang(c, it, tgl, pihak, qty, harga, nominal, cara, produk, ket, akun_pilih, hasil)
        jid, no = ju.catat_otomatis(c, tgl, r["ket"], r["jurnal"], r["prefix"], bukti)
        psd.catat_mutasi(c, tgl, r["ket"], jid, r["mutasi"])
        c.execute("INSERT INTO transaksi (kelompok,item,no_bukti,tanggal,pihak,jenis,qty,harga,total,cara,keterangan,jurnal_id) "
                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                  (it["kelompok"], it["nama"], no, tgl, (pihak or "").strip(), r["jenis"], r["qty"], r["harga"], r["total"],
                   r["cara"], (ket or "").strip(), jid))
    return no


def hapus(jid):
    """Hapus transaksi beserta jurnal dan mutasi stoknya."""
    if not ambil("SELECT id FROM transaksi WHERE jurnal_id=%s", jid):
        raise ValueError("Transaksi tidak ditemukan.")
    psd.pastikan_terakhir(jid)
    with cursor(True) as c:
        c.execute("DELETE FROM persediaan_mutasi WHERE jurnal_id=%s", (jid,))
        c.execute("DELETE FROM transaksi WHERE jurnal_id=%s", (jid,))
        c.execute("DELETE FROM jurnal WHERE id=%s", (jid,))


# ------------------------------------------------------------------ tabel riwayat
def tabel(kelompok):
    kolom = kol(("Tanggal", 105, "w"), ("No. Bukti", 100, "w"), ("Jenis Transaksi", 240, "w"), ("Customer / Supplier / Nama", 170, "w"),
                ("Keterangan", 250, "w"), ("Jumlah kg", 90, "e"), ("Harga/kg", 110, "e"), ("Total (Rp)", 140, "e"), ("Pembayaran", 130, "w"))
    rows, tq, tt = [], Z, Z
    for r in ambil("SELECT * FROM transaksi WHERE kelompok=%s ORDER BY tanggal,id", kelompok):
        q, t = dec(r["qty"]), dec(r["total"])
        tq, tt = tq + q, tt + t
        rows.append(B(r["tanggal"], r["no_bukti"], r["item"], r["pihak"], r["keterangan"], q, dec(r["harga"]), t, r["cara"]))
    return kolom, (rows or [B("", "", "Belum ada transaksi.", tag="kosong")]) + [B("", "", "TOTAL", "", "", tq, None, tt, "", tag="b")]


def tabel_terima(b):
    return tabel("TERIMA")


def tabel_keluar(b):
    return tabel("KELUAR")


def tabel_lain(b):
    return tabel("LAIN")


# ------------------------------------------------------------------ halaman
def halaman(kelompok):
    meta = KELOMPOK[kelompok]
    akun = ambil("SELECT kode,nama,kelompok FROM akun ORDER BY kode")
    nama_akun = {a["kode"]: a["nama"] for a in akun}
    ada = set(nama_akun)
    items = [i for i in ITEM if i["kelompok"] == kelompok and tersedia(i, akun)]
    st.markdown(f"<div class='catatan'>{meta['catatan']}</div>", unsafe_allow_html=True)
    if not items:
        st.warning("Semua jenis transaksi di bagian ini tidak tersedia karena akun yang dibutuhkan sudah dihapus. Tambahkan kembali akunnya di Daftar Akun.")
        return
    v = st.session_state.setdefault(f"v_{kelompok}", 0)

    # --- 1. pilih jenis
    bagian("Pilih jenis transaksi", 1)
    keys = [i["k"] for i in items]
    if st.session_state.get(f"jt_{kelompok}") not in keys:
        st.session_state.pop(f"jt_{kelompok}", None)
    it = ITEM_K[st.selectbox("Jenis transaksi", keys, format_func=lambda k: ITEM_K[k]["nama"], key=f"jt_{kelompok}")]
    if it["info"]:
        st.caption(it["info"])

    # --- 2. isi data
    bagian("Isi data transaksi", 2)
    kk = f"{kelompok}_{it['k']}_{v}"
    produk, qty, harga, nominal, cara, akun_pilih, hasil = None, 0.0, 0.0, 0.0, None, None, 0.0
    c = st.columns(3)
    tgl = c[0].date_input("Tanggal", dt.date.today(), format="DD/MM/YYYY", key=f"t_{kk}")
    no = c[1].text_input("No. bukti (kosong = otomatis)", key=f"n_{kk}")
    pihak = c[2].text_input(it["label_pihak"], key=f"p_{kk}")

    def isian_cara(kolom):
        """Kas / bank bila tunai, atau keterangan akun lawan (piutang / utang) bila kredit."""
        if pakai_cara(it):
            return kolom.selectbox(meta["label_cara"] or "Pembayaran", list(opsi_cara(ada)), key=f"c_{kk}")
        lawan = it["lawan"] if _jual_beli(it) else it["kr"]
        kolom.text_input("Pembayaran", f"Kredit ({nama_akun.get(lawan, lawan)})", disabled=True, key=f"cf_{kk}")
        return None

    if _jual_beli(it):
        jual = it["tipe"] == "jual"
        pk = produk_ok(it, ada)
        c = st.columns(4)
        if len(pk) > 1:
            produk = c[0].selectbox("Jenis barang", pk, format_func=lambda x: (psd.PRODUK if jual else psd.BELI)[x]["nama"], key=f"pk_{kk}")
        else:
            produk = pk[0]
            c[0].text_input("Jenis barang", (psd.PRODUK if jual else psd.BELI)[produk]["nama"], disabled=True, key=f"pkf_{kk}")
        qty = c[1].number_input("Jumlah (kg)", min_value=0.0, step=1.0, format="%.2f", key=f"q_{kk}")
        harga = c[2].number_input("Harga jual per kg (Rp)" if jual else "Harga beli per kg (Rp)", min_value=0.0, step=500.0, format="%.0f", key=f"h_{kk}")
        cara = isian_cara(c[3])
    elif it["tipe"] == "olah":
        c = st.columns(2)
        qty = c[0].number_input("Alpukat segar yang diolah (kg)", min_value=0.0, step=1.0, format="%.2f", key=f"q_{kk}")
        hasil = c[1].number_input("Hasil frozen (kg)", min_value=0.0, step=1.0, format="%.2f", key=f"hs_{kk}")
    else:
        c = st.columns(3 if it["pilih"] else 2)
        nominal = c[0].number_input("Nominal (Rp)", min_value=0.0, step=10000.0, format="%.0f", key=f"nm_{kk}")
        cara = isian_cara(c[1])
        if it["pilih"]:
            opsi = opsi_pilih(it, akun)
            akun_pilih = c[2].selectbox("Akun", [k for k, _ in opsi], format_func=lambda k: f"{k}  {nama_akun[k]}", key=f"ap_{kk}")
    ket = st.text_input("Keterangan (misalnya jenis barang, tujuan, atau catatan)", key=f"k_{kk}")

    # --- ringkasan dan pratinjau jurnal
    total = angka(qty) * angka(harga) if _jual_beli(it) else angka(nominal)
    if total:
        tambah = ""
        if _jual_beli(it) and not pakai_cara(it):
            tambah = " &nbsp;(belum dibayar, dicatat sebagai " + ("piutang)" if it["lawan"] == "1-103" else "utang)")
        st.markdown(f"<div class='total-box'>Total transaksi <span>Rp {rp(total, '0')}</span>{tambah}</div>", unsafe_allow_html=True)
    if it["tipe"] == "jual":
        sk = psd.PRODUK[produk]["stok"]
        q0, n0 = psd.stok(sk)
        st.caption(f"Stok tersedia {psd.kgs(q0)} kg, harga pokok rata-rata Rp {rp(n0 / q0 if q0 else 0, '0')} per kg")
    elif it["tipe"] == "olah":
        q0, _ = psd.stok("1-104")
        st.caption(f"Stok segar tersedia {psd.kgs(q0)} kg")

    if qty or harga or nominal or hasil:
        try:
            with cursor() as cc:
                r = rancang(cc, it, tgl, pihak, qty, harga, nominal, cara, produk, ket, akun_pilih, hasil)
            bagian("Jurnal yang akan terbentuk otomatis", 3)
            rows = [B(k, (I if kr else "") + nama_akun.get(k, k), d, kr) for k, d, kr in r["jurnal"] if d or kr]
            tampil(kol(("Kode", 80, "w"), ("Akun", 430, "w"), ("Debit", 150, "e"), ("Kredit", 150, "e")),
                   rows + [B("", "TOTAL", sum(x[1] for x in r["jurnal"]), sum(x[2] for x in r["jurnal"]), tag="b")])
        except ValueError as e:
            st.warning(str(e))

    simpan_no = {}

    def aksi():
        simpan_no["no"] = simpan(it["k"], tgl, pihak, qty, harga, nominal, cara, produk, ket, akun_pilih, hasil, no)

    if st.button(f"Simpan {meta['judul'].lower()}", type="primary", key=f"s_{kk}") and jalankan(aksi):
        st.session_state[f"v_{kelompok}"] = v + 1
        pesan("ok", f"Tersimpan dengan bukti {simpan_no['no']}. Jurnal umum, kartu stok, dan buku besar sudah ikut diperbarui.")
        st.rerun()

    # --- riwayat
    bagian(f"Riwayat {meta['judul'].lower()}")
    tampil(*tabel(kelompok))
    pilih_hapus(kelompok, "Hapus transaksi", ambil("SELECT jurnal_id,no_bukti,tanggal,pihak,item,total FROM transaksi WHERE kelompok=%s ORDER BY tanggal,id", kelompok),
                lambda r: f"{r['no_bukti']}   {tgl_teks(r['tanggal'])}   {r['item']}   {r['pihak'] or ''}   Rp {rp(r['total'], '0')}",
                lambda r: hapus(r["jurnal_id"]))
