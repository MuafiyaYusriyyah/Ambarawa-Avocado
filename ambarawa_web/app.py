"""Ambarawa Avocado - Siklus Akuntansi (Streamlit + MySQL).   Jalankan: streamlit run app.py"""
import datetime as dt
import html
import io

import pandas as pd
import streamlit as st

import akuntansi as ak
import db
import export
import persediaan as psd
from akuntansi import D, Z, rp

# Halaman admin
st.set_page_config(page_title="Alpukat Ambarawa", layout="wide")

# 1. Inisialisasi status login di session_state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ==========================================
# HALAMAN LOGIN 
# ==========================================
if not st.session_state.logged_in:
    # Buat tampilan center/rapi untuk login 
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🔐 Login Admin")
        st.write("Silakan masukkan akun admin untuk mengakses sistem.")
        
        with st.form("form_login_terpisah"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            tombol_submit = st.form_submit_button("Masuk ke Aplikasi", use_container_width=True)
            
            if tombol_submit:
                # Cek data dari secrets.toml
                if username_input == st.secrets["admin"]["username"] and password_input == st.secrets["admin"]["password"]:
                    st.session_state.logged_in = True
                    st.success("Login berhasil! Memuat sistem...")
                    st.rerun()
                else:
                    st.error("Username atau password salah!")
                    
    # Hentikan eksekusi kode di bawah agar menu lain tidak ikut tampil sebelum login
    st.stop()

# ==========================================
# HALAMAN UTAMA (HANYA MUNCUL SETELAH LOGIN)
# ==========================================

# Tombol Logout di sidebar bagian atas
if st.sidebar.button("Keluar (Logout)"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.success("Status: Aktif sebagai Admin")
st.sidebar.markdown("---")

# --- MASUKKAN SEMUA KODE SIKLUS AKUNTANSI ASLIMU DI BAWAH INI ---
# Contoh:
st.title("📊 Sistem Informasi Akuntansi - Alpukat Ambarawa")
st.write("Selamat datang di panel utama siklus akuntansi!")

st.markdown("""<style>
.stApp{background:#f5f6f3}
[data-testid="stSidebar"]{background:#2f5d3a}
[data-testid="stSidebar"] *{color:#fff}
[data-testid="stSidebar"] button{width:100%;justify-content:flex-start;text-align:left;border:0;background:transparent;box-shadow:none}
[data-testid="stSidebar"] button:hover{background:rgba(255,255,255,.14)}
[data-testid="stSidebar"] button[kind="primary"],[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]{background:#fff;font-weight:700}
[data-testid="stSidebar"] button[kind="primary"] *,[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] *{color:#2f5d3a!important}
h1{color:#2f5d3a;font-size:1.9rem!important;border-bottom:2px solid #2f5d3a;padding-bottom:.6rem}
.tbl{overflow:auto;max-height:68vh;background:#fff;border:1px solid #d9ddd6;border-radius:4px;margin-bottom:1rem}
.tbl table{border-collapse:collapse;width:100%;font-size:14px}
.tbl th{position:sticky;top:0;background:#2f5d3a;color:#fff;text-align:left;padding:9px 12px;white-space:nowrap}
.tbl td{padding:7px 12px;border-bottom:1px solid #e6e9e3;white-space:pre-wrap;color:#262b25}
.tbl .e{text-align:right;font-variant-numeric:tabular-nums}
.tbl tr.b td{font-weight:700}
.tbl tr.kosong td{color:#6b726b;font-style:italic}
</style>""", unsafe_allow_html=True)

CEPAT = [("Penyusutan peralatan", "Penyusutan peralatan periode ini", "7-105", "1-108"),
         ("Gaji terutang", "Gaji pekerja yang masih terutang", "7-101", "2-102")]
NAN = float("nan")


# ============================================================ komponen kecil
def num(x):
    """Isi sel / kolom angka -> Decimal (kosong dianggap 0)."""
    return ak.angka(x) if x is not None and not pd.isna(x) else Z


def pesan(jenis, teks):
    st.session_state["pesan"] = (jenis, teks)


def buka(halaman):
    st.session_state["hal"] = halaman


def jalankan(fn, *arg):
    """Salah input tampil sebagai pesan merah. Mengembalikan True bila berhasil."""
    try:
        fn(*arg)
        return True
    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"{e}\n\nPeriksa koneksi MySQL (secrets atau config.py) dan pastikan database menyala.")
    return False


def fmt(sel, tag):
    """Sel tabel -> teks. Angka nol ditulis kosong, kecuali pada baris tebal (jumlah dan total)."""
    if isinstance(sel, dt.date):
        return ak.tgl(sel)
    if isinstance(sel, D):
        return rp(sel, "0" if tag == "b" else "")
    return "" if sel is None else str(sel)


def tampil(kolom, baris):
    """Tabel HTML polos. baris = (isi sel, tag, iid)."""
    th = "".join(f"<th class='{'e' if r == 'e' else ''}'>{html.escape(j)}</th>" for j, _, r in kolom)
    tr = []
    for isi, tag, *_ in baris:
        sel = [fmt(x, tag) for x in isi] + [""] * (len(kolom) - len(isi))
        tr.append(f"<tr class='{tag or ''}'>" + "".join(
            f"<td class='{'e' if kolom[i][2] == 'e' else ''}'>{html.escape(s)}</td>" for i, s in enumerate(sel)) + "</tr>")
    st.markdown(f"<div class='tbl'><table><thead><tr>{th}</tr></thead><tbody>{''.join(tr)}</tbody></table></div>", unsafe_allow_html=True)


def hal_tabel(bagian, tab=False):
    """Halaman laporan: satu atau beberapa tabel dari ak.TABEL."""
    b = ak.Buku()
    if tab:
        for t, (_, kunci) in zip(st.tabs([n for n, _ in bagian]), bagian):
            with t:
                tampil(*ak.TABEL[kunci](b))
    else:
        for nama, kunci in bagian:
            if nama:
                st.subheader(nama)
            tampil(*ak.TABEL[kunci](b))


def pilih_hapus(kunci, judul, daftar, label, aksi):
    """Kotak hapus: pilih satu baris dari daftar lalu hapus."""
    if not daftar:
        return
    with st.expander(judul):
        i = st.selectbox("Pilih", range(len(daftar)), format_func=lambda i: label(daftar[i]), key=f"sel_{kunci}")
        if st.button(judul, key=f"hps_{kunci}") and jalankan(aksi, daftar[i]):
            pesan("ok", "Data dihapus.")
            st.rerun()


# ============================================================ halaman lihat
def hal_jurnal(jenis):
    tampil(*ak.tabel_jurnal(jenis))
    pilih_hapus(jenis, "Hapus jurnal", db.ambil("SELECT id,tanggal,bukti,keterangan FROM jurnal WHERE jenis=%s AND sumber='MANUAL' ORDER BY tanggal,id", jenis),
                lambda r: f"{r['bukti']}   {ak.tgl(r['tanggal'])}   {r['keterangan'] or ''}", lambda r: ak.hapus_jurnal(r["id"]))


def hal_nota(tipe):
    tampil(*ak.tabel_nota(tipe))
    pilih_hapus(tipe, "Hapus nota", db.ambil("SELECT jurnal_id,no_nota,tanggal,pihak,jenis,total FROM nota WHERE tipe=%s ORDER BY tanggal,id", tipe),
                lambda r: f"{r['no_nota']}   {ak.tgl(r['tanggal'])}   {r['pihak']}   {r['jenis']}   Rp {rp(r['total'], '0')}",
                lambda r: psd.hapus(r["jurnal_id"]))


def hal_persediaan():
    b = ak.Buku()
    for kode, kunci in (("1-104", "k104"), ("1-105", "k105")):
        st.subheader(f"Kartu stok {ak.STOK[kode]}")
        kolom, rows = ak.TABEL[kunci](b)
        tampil(kolom, rows)
        terakhir = next((r[2] for r in reversed(rows) if len(r) > 2 and r[2]), None)       # id jurnal transaksi terakhir
        if terakhir and st.button(f"Hapus transaksi terakhir {ak.STOK[kode]}", key=f"hs_{kode}") and jalankan(psd.hapus, int(terakhir)):
            pesan("ok", "Transaksi terakhir dihapus.")
            st.rerun()


def hal_penutup():
    if st.button("Simpan jurnal penutup ke database", type="primary") and jalankan(ak.simpan_penutup):
        pesan("ok", "Jurnal penutup tersimpan di database.")
        st.rerun()
    tampil(*ak.Buku().tabel_penutup())


def hal_akun():
    with st.form("form_akun", clear_on_submit=True):
        c = st.columns([1, 3, 1.5, 1.2])
        kode, nama = c[0].text_input("Kode"), c[1].text_input("Nama akun")
        kel = c[2].selectbox("Kelompok", ["Aset", "Liabilitas", "Ekuitas", "Pendapatan", "Pembelian", "HPP", "Beban"])
        normal = c[3].selectbox("Saldo normal", ["Debit", "Kredit"])
        ok = st.form_submit_button("Tambah akun")
    if ok and jalankan(ak.tambah_akun, kode, nama, kel, "D" if normal == "Debit" else "K"):
        pesan("ok", f"Akun {kode} ditambahkan.")
        st.rerun()
    tampil(*ak.TABEL["akun"](ak.Buku()))


def hal_beranda():
    st.subheader("Input data")
    tombol = [("Input Saldo Awal", "in_saldo"), ("Input Jurnal Umum", "in_ju"), ("Input Jurnal Penyesuaian", "in_ajp"),
              ("Input Penjualan", "in_jual"), ("Input Pembelian", "in_beli"), ("Input Produksi Frozen", "in_olah")]
    for baris in (tombol[:3], tombol[3:]):
        for kol, (teks, k) in zip(st.columns(3), baris):
            kol.button(teks, key=f"bi_{k}", on_click=buka, args=(k,), type="primary")
    b = ak.Buku()
    n = {r["jenis"]: r["n"] for r in db.ambil("SELECT jenis, COUNT(*) n FROM jurnal GROUP BY jenis")}
    awal = any(d or k for d, k, _ in b.sa.values())
    _, rows = b.saldo()
    td, tkr = rows[-1][0][2], rows[-1][0][3]
    langkah = [("saldo_awal", "Saldo awal", "sudah terisi" if awal else "belum diisi", awal),
               ("ju", "Jurnal umum", f"{n.get('JU', 0)} jurnal", bool(n.get("JU"))), ("bb", "Buku besar", "otomatis", True),
               ("ns", "Neraca saldo", "seimbang" if td == tkr and td else "menunggu data", bool(td) and td == tkr),
               ("ajp", "Jurnal penyesuaian", f"{n.get('AJP', 0)} jurnal", bool(n.get("AJP"))), ("nl", "Neraca lajur", "otomatis", True),
               ("lap", "Laporan keuangan", "otomatis", True), ("pnt", "Jurnal penutup", "tersimpan" if n.get("PNT") else "belum disimpan", bool(n.get("PNT")))]
    kiri, kanan = st.columns([3, 2])
    with kiri:
        st.subheader("Alur siklus")
        for kunci, teks, ket, selesai in langkah:
            c = st.columns([0.5, 3, 2])
            c[0].write("●" if selesai else "○")
            c[1].button(teks, key=f"al_{kunci}", on_click=buka, args=(kunci,))
            c[2].caption(ket)
    with kanan:
        st.subheader("Periode")
        with st.form("form_periode"):
            usaha, periode = st.text_input("Nama usaha", b.pg["nama_usaha"]), st.text_input("Nama periode", b.pg["nama_periode"])
            c = st.columns(2)
            a, z = c[0].date_input("Tanggal awal", b.pg["tgl_awal"], format="DD/MM/YYYY"), c[1].date_input("Tanggal akhir", b.pg["tgl_akhir"], format="DD/MM/YYYY")
            ok = st.form_submit_button("Simpan periode")
        if ok and jalankan(ak.simpan_periode, usaha, periode, a.strftime("%d-%m-%Y"), z.strftime("%d-%m-%Y")):
            pesan("ok", "Periode disimpan.")
            st.rerun()


# ============================================================ halaman input (dibuka dari Beranda)
def hal_in_saldo():
    akun = ak.akun_awal()
    df = pd.DataFrame([{"Kode": a["kode"], "Nama Akun": a["nama"], "Sisi": "Debit" if a["saldo_normal"] == "D" else "Kredit",
                        "Saldo (Rp)": float(ak.dec(a["debit"] if a["saldo_normal"] == "D" else a["kredit"])),
                        "Jumlah (kg)": float(ak.dec(a["qty"]))} for a in akun])
    ed = st.data_editor(df, hide_index=True, key="ed_awal", disabled=["Kode", "Nama Akun", "Sisi"],
                        column_config={"Saldo (Rp)": st.column_config.NumberColumn(min_value=0, step=1000),
                                       "Jumlah (kg)": st.column_config.NumberColumn(min_value=0, help="Isi hanya untuk akun persediaan")})
    isian, d, k = {}, Z, Z
    for a, (_, r) in zip(akun, ed.iterrows()):
        v = num(r["Saldo (Rp)"])
        isian[a["kode"]] = (v, num(r["Jumlah (kg)"]) if a["kode"] in ak.STOK else Z)
        d, k = (d + v, k) if a["saldo_normal"] == "D" else (d, k + v)
    st.markdown(f"**Total debit Rp {rp(d, '0')}      Total kredit Rp {rp(k, '0')}      Selisih Rp {rp(d - k, '0')}**")
    if st.button("Simpan saldo awal", type="primary") and jalankan(ak.simpan_saldo_awal, isian):
        pesan("ok" if d == k else "peringatan", "Saldo awal tersimpan." + ("" if d == k else " Namun total debit dan kredit belum seimbang."))
        st.rerun()


def hal_in_jurnal(jenis, prefix, nama, cepat=()):
    """Form jurnal umum atau penyesuaian. Tabel baris akun bisa ditambah, debit harus sama dengan kredit."""
    v = st.session_state.setdefault(f"v_{jenis}", 0)
    opsi = [f"{a['kode']}  {a['nama']}" for a in db.ambil("SELECT kode,nama FROM akun WHERE kode<>'3-103' ORDER BY kode")]
    kosong = lambda: pd.DataFrame({"Akun": pd.Series([None] * 4, dtype="object"), "Debit": pd.Series([NAN] * 4), "Kredit": pd.Series([NAN] * 4)})
    awal = st.session_state.get(f"df_{jenis}")
    c = st.columns([1, 1, 3])
    tgl = c[0].date_input("Tanggal", dt.date.today(), format="DD/MM/YYYY", key=f"t_{jenis}_{v}")
    bukti = c[1].text_input("No. bukti (kosong = otomatis)", key=f"b_{jenis}_{v}")
    ket = c[2].text_input("Keterangan", value=st.session_state.get(f"kt_{jenis}", ""), key=f"k_{jenis}_{v}")
    if cepat:
        st.caption("Isi cepat")
        for kol, (teks, kt, d, k) in zip(st.columns(len(cepat) + 2), cepat):
            if kol.button(teks, key=f"c_{jenis}_{d}"):
                cari = lambda kode: next((o for o in opsi if o.startswith(kode + " ")), None)
                st.session_state[f"df_{jenis}"] = pd.DataFrame({"Akun": pd.Series([cari(d), cari(k), None, None], dtype="object"),
                                                                "Debit": pd.Series([NAN] * 4), "Kredit": pd.Series([NAN] * 4)})
                st.session_state[f"kt_{jenis}"], st.session_state[f"v_{jenis}"] = kt, v + 1
                st.rerun()
    df = st.data_editor(kosong() if awal is None else awal, num_rows="dynamic", hide_index=True, key=f"e_{jenis}_{v}",
                        column_config={"Akun": st.column_config.SelectboxColumn("Akun", options=opsi, width="large"),
                                       "Debit": st.column_config.NumberColumn("Debit", min_value=0, step=1000),
                                       "Kredit": st.column_config.NumberColumn("Kredit", min_value=0, step=1000)})
    d, k = sum((num(x) for x in df["Debit"]), Z), sum((num(x) for x in df["Kredit"]), Z)
    st.markdown(f"**Total debit Rp {rp(d, '0')}      Total kredit Rp {rp(k, '0')}**")
    if d or k:
        (st.success if d == k else st.warning)("Seimbang" if d == k else f"Belum seimbang, selisih Rp {rp(abs(d - k))}")
    if st.button(f"Simpan {nama.lower()}", type="primary", key=f"s_{jenis}"):
        baris = [(a.split()[0] if isinstance(a, str) and a else "", num(x), num(y)) for a, x, y in zip(df["Akun"], df["Debit"], df["Kredit"])]
        if jalankan(ak.simpan_jurnal, jenis, prefix, tgl.strftime("%d-%m-%Y"), bukti, ket, baris):
            st.session_state.pop(f"df_{jenis}", None)
            st.session_state.pop(f"kt_{jenis}", None)
            st.session_state[f"v_{jenis}"] = v + 1
            pesan("ok", f"{nama} tersimpan dan sudah masuk ke buku besar.")
            st.rerun()


def hal_in_nota(tipe):
    """Input nota penjualan / pembelian: otomatis menjadi jurnal umum, kartu stok, dan buku besar."""
    jual = tipe == "JUAL"
    v = st.session_state.setdefault(f"v_{tipe}", 0)
    jenis_opsi = {k: p["nama"] for k, p in (psd.PRODUK if jual else psd.BELI).items()}
    akun_opsi = psd.JUAL_AKUN if jual else psd.BELI_AKUN
    c = st.columns(3)
    tgl = c[0].date_input("Tanggal", dt.date.today(), format="DD/MM/YYYY", key=f"nt_{tipe}_{v}")
    nota = c[1].text_input("No. nota (kosong = otomatis)", key=f"nn_{tipe}_{v}")
    pihak = c[2].text_input("Nama customer" if jual else "Nama supplier", key=f"np_{tipe}_{v}")
    c = st.columns(4)
    jenis = c[0].selectbox("Jenis barang", list(jenis_opsi), format_func=jenis_opsi.get, key=f"nj_{tipe}_{v}")
    qty = c[1].number_input("Jumlah (kg)", min_value=0.0, step=1.0, format="%.2f", key=f"nq_{tipe}_{v}")
    harga = c[2].number_input("Harga jual per kg (Rp)" if jual else "Harga beli per kg (Rp)", min_value=0.0, step=500.0, key=f"nh_{tipe}_{v}")
    cara = c[3].selectbox("Pembayaran", list(akun_opsi), key=f"nc_{tipe}_{v}")
    total = ak.angka(qty) * ak.angka(harga)
    st.markdown(f"**Total {'penjualan' if jual else 'pembelian'}: Rp {rp(total, '0')}**" + ("   (belum dibayar, masuk " + ("piutang usaha)" if jual else "utang usaha)") if cara == "Kredit" else ""))
    if jual:
        q, n = psd.stok(psd.PRODUK[jenis]["stok"])
        st.caption(f"Stok tersedia {psd.kgs(q)} kg, harga pokok rata-rata Rp {rp(n / q if q else 0, '0')} per kg")
    if st.button("Simpan penjualan" if jual else "Simpan pembelian", type="primary", key=f"sn_{tipe}"):
        if jalankan(psd.jual if jual else psd.beli, tgl, jenis, ak.angka(qty), ak.angka(harga), cara, nota, pihak):
            st.session_state[f"v_{tipe}"] = v + 1
            pesan("ok", "Nota tersimpan. Jurnal umum, kartu stok, dan buku besar sudah ikut diperbarui.")
            st.rerun()


def hal_in_olah():
    v = st.session_state.setdefault("v_olah", 0)
    c = st.columns(4)
    tgl = c[0].date_input("Tanggal", dt.date.today(), format="DD/MM/YYYY", key=f"ot{v}")
    qs = c[1].number_input("Segar diolah (kg)", min_value=0.0, step=1.0, format="%.2f", key=f"oq{v}")
    qf = c[2].number_input("Hasil frozen (kg)", min_value=0.0, step=1.0, format="%.2f", key=f"of{v}")
    ket = c[3].text_input("Keterangan", key=f"ok{v}")
    if st.button("Simpan produksi", type="primary") and jalankan(psd.olah, tgl, ak.angka(qs), ak.angka(qf), ket):
        st.session_state["v_olah"] = v + 1
        pesan("ok", "Produksi frozen tersimpan.")
        st.rerun()


# ============================================================ susunan aplikasi
T = lambda *bagian, tab=False: (lambda: hal_tabel(list(bagian), tab))
HALAMAN = {
    "beranda": ("Beranda", hal_beranda), "akun": ("Daftar Akun", hal_akun), "saldo_awal": ("Saldo Awal", T((None, "awal"))),
    "jual": ("Penjualan", lambda: hal_nota("JUAL")), "beli": ("Pembelian", lambda: hal_nota("BELI")),
    "ju": ("Jurnal Umum", lambda: hal_jurnal("JU")), "persediaan": ("Persediaan", hal_persediaan),
    "bb": ("Buku Besar", T((None, "bb"))), "ns": ("Neraca Saldo", T((None, "ns"))),
    "ajp": ("Jurnal Penyesuaian", lambda: hal_jurnal("AJP")), "bb_ajp": ("Buku Besar Setelah Penyesuaian", T((None, "bb_ajp"))),
    "nl": ("Neraca Lajur", T((None, "nl"))),
    "lap": ("Laporan Keuangan", T(("📈 Laba Rugi", "lr"), ("⚖ Perubahan Ekuitas", "ek"), ("🏦 Posisi Keuangan", "pos"), tab=True)),
    "pnt": ("Jurnal Penutup", hal_penutup), "nsa": ("Neraca Saldo Akhir", T((None, "nsa"))),
    "in_saldo": ("Input Saldo Awal", hal_in_saldo), "in_ju": ("Input Jurnal Umum", lambda: hal_in_jurnal("JU", "JU", "Jurnal Umum")),
    "in_ajp": ("Input Jurnal Penyesuaian", lambda: hal_in_jurnal("AJP", "AJP", "Jurnal Penyesuaian", CEPAT)),
    "in_jual": ("Input Penjualan", lambda: hal_in_nota("JUAL")), "in_beli": ("Input Pembelian", lambda: hal_in_nota("BELI")),
    "in_olah": ("Input Produksi Frozen", hal_in_olah),
}
MENU = [("Persiapan", [("beranda", "Beranda"), ("akun", "Daftar Akun"), ("saldo_awal", "0. Saldo Awal")]),
        ("Transaksi", [("jual", "Penjualan"), ("beli", "Pembelian")]),
        ("Siklus Akuntansi", [("ju", "1. Jurnal Umum"), ("persediaan", "Persediaan"), ("bb", "2. Buku Besar"), ("ns", "3. Neraca Saldo"),
                              ("ajp", "4. Jurnal Penyesuaian"), ("bb_ajp", "5. Buku Besar Setelah Penyesuaian"), ("nl", "6. Neraca Lajur"),
                              ("lap", "7. Laporan Keuangan"), ("pnt", "8. Jurnal Penutup"), ("nsa", "9. Neraca Saldo Akhir")])]


@st.cache_resource(show_spinner=False)
def siap():
    db.siapkan_database()
    return True


def gerbang():
    """Kata sandi opsional: aktif bila app_password diisi di secrets."""
    try:
        sandi = st.secrets.get("app_password")
    except Exception:
        sandi = None
    if sandi and not st.session_state.get("masuk"):
        st.title("Ambarawa Avocado")
        x = st.text_input("Kata sandi", type="password")
        if st.button("Masuk", type="primary"):
            if x == str(sandi):
                st.session_state["masuk"] = True
                st.rerun()
            st.error("Kata sandi salah.")
        st.stop()


def main():
    gerbang()
    try:
        siap()
    except Exception as e:
        st.error(f"Tidak bisa terhubung ke MySQL: {e}")
        st.info("Periksa .streamlit/secrets.toml (atau config.py) dan pastikan MySQL menyala.")
        st.stop()
    hal = st.session_state.setdefault("hal", "beranda")
    aktif = "beranda" if hal.startswith("in_") else hal
    with st.sidebar:
        st.markdown("### Ambarawa Avocado")
        for judul, items in MENU:
            st.caption(judul.upper())
            for k, teks in items:
                st.button(teks, key=f"m_{k}", on_click=buka, args=(k,), type="primary" if k == aktif else "secondary")
        st.caption("EXPORT")
        if st.button("Siapkan file Excel", key="m_xlsx"):
            buf = io.BytesIO()
            export.buat_excel(buf)
            st.session_state["xlsx"] = buf.getvalue()
        if "xlsx" in st.session_state:
            st.download_button("Unduh Excel", st.session_state["xlsx"], "Siklus_Akuntansi_Ambarawa_Avocado.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    judul, fungsi = HALAMAN[hal]
    st.title(judul)
    if hal.startswith("in_"):
        st.button("Kembali ke Beranda", on_click=buka, args=("beranda",), key="kembali")
    if "pesan" in st.session_state:
        jenis, teks = st.session_state.pop("pesan")
        (st.success if jenis == "ok" else st.warning)(teks)
    fungsi()


if __name__ == "__main__":
    main()
