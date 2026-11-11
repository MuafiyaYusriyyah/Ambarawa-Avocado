"""TAHAP 1 - JURNAL UMUM.
Jurnal umum terisi dari dua sumber:
  1. otomatis, dari input Penerimaan / Pengeluaran / Transaksi Lainnya (lihat transaksi.py)
  2. manual, lewat form Input Jurnal Umum di file ini
Jurnal Penyesuaian (ajp.py) memakai tabel dan form yang sama, hanya jenisnya 'AJP'."""
import datetime as dt

import pandas as pd
import streamlit as st

from core.db import ambil, cursor
from core.util import I, Z, B, angka, dec, kol, rp, tanggal, tgl as tgl_teks
from ui.komponen import NAN, jalankan, num, pesan, pilih_hapus, tampil

KOL_JURNAL = kol(("Tanggal", 105, "w"), ("Bukti", 90, "w"), ("Keterangan / Akun", 430, "w"), ("Ref", 70, "w"), ("Debit", 140, "e"), ("Kredit", 140, "e"))


# ------------------------------------------------------------------ simpan
def simpan_jurnal(jenis, prefix, tgl_s, bukti, ket, baris):
    """Jurnal manual. baris: [(kode, debit, kredit)]. Jurnal harus seimbang."""
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


def catat_otomatis(c, tgl, ket, baris, prefix, bukti=""):
    """Jurnal umum otomatis dari sebuah transaksi (dipanggil transaksi.py di dalam satu transaksi database).
    baris: [(kode, debit, kredit)]. Mengembalikan (id jurnal, nomor bukti)."""
    bukti = bukti.strip()
    c.execute("INSERT INTO jurnal (tanggal,bukti,keterangan,jenis,sumber) VALUES (%s,%s,%s,'JU','TRANSAKSI')", (tgl, bukti, ket))
    jid = c.lastrowid
    if not bukti:
        bukti = f"{prefix}-{jid:04d}"
        c.execute("UPDATE jurnal SET bukti=%s WHERE id=%s", (bukti, jid))
    for x in baris:
        c.execute("INSERT INTO jurnal_detail (jurnal_id,kode,debit,kredit) VALUES (%s,%s,%s,%s)", (jid, *x))
    return jid, bukti


def hapus_jurnal(jid):
    r = ambil("SELECT sumber FROM jurnal WHERE id=%s", jid)
    if not r:
        raise ValueError("Jurnal tidak ditemukan.")
    if r[0]["sumber"] != "MANUAL":
        raise ValueError("Jurnal ini dibuat otomatis dari transaksi. Hapus lewat halaman transaksinya.")
    with cursor(True) as c:
        c.execute("DELETE FROM jurnal WHERE id=%s", (jid,))


# ------------------------------------------------------------------ tabel
def tabel_jenis(jenis):
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
        rows = [B("", "", "Belum ada jurnal. Catat lewat menu Input Transaksi di sebelah kiri.", tag="kosong")]
    return KOL_JURNAL, rows + [B("", "", "TOTAL", "", td, tk, tag="b")]


def tabel(b):
    return tabel_jenis("JU")


# ------------------------------------------------------------------ halaman
def halaman_jenis(jenis):
    tampil(*tabel_jenis(jenis))
    pilih_hapus(jenis, "Hapus jurnal", ambil("SELECT id,tanggal,bukti,keterangan FROM jurnal WHERE jenis=%s AND sumber='MANUAL' ORDER BY tanggal,id", jenis),
                lambda r: f"{r['bukti']}   {tgl_teks(r['tanggal'])}   {r['keterangan'] or ''}", lambda r: hapus_jurnal(r["id"]))


def halaman():
    st.caption("Jurnal bertanda [otomatis] berasal dari input Penerimaan, Pengeluaran, dan Transaksi Lainnya. Hapus lewat halaman transaksinya.")
    halaman_jenis("JU")


def form_input(jenis, prefix, nama, cepat=()):
    """Form jurnal manual (umum atau penyesuaian). Baris akun bisa ditambah, debit harus sama dengan kredit."""
    v = st.session_state.setdefault(f"v_{jenis}", 0)
    opsi = [f"{a['kode']}  {a['nama']}" for a in ambil("SELECT kode,nama FROM akun WHERE kode<>'3-103' ORDER BY kode")]
    kosong = lambda: pd.DataFrame({"Akun": pd.Series([None] * 4, dtype="object"), "Debit": pd.Series([NAN] * 4), "Kredit": pd.Series([NAN] * 4)})
    awal = st.session_state.get(f"df_{jenis}")
    c = st.columns([1, 1, 3])
    tgl = c[0].date_input("Tanggal", dt.date.today(), format="DD/MM/YYYY", key=f"t_{jenis}_{v}")
    bukti = c[1].text_input("No. bukti (kosong = otomatis)", key=f"b_{jenis}_{v}")
    ket = c[2].text_input("Keterangan", value=st.session_state.get(f"kt_{jenis}", ""), key=f"k_{jenis}_{v}")
    if cepat:
        st.caption("Isi cepat")
        for kolom, (teks, kt, d, k) in zip(st.columns(len(cepat) + 2), cepat):
            if kolom.button(teks, key=f"c_{jenis}_{d}"):
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
    st.markdown(f"<div class='total-box'>Total debit <span>Rp {rp(d, '0')}</span> &nbsp;·&nbsp; Total kredit <span>Rp {rp(k, '0')}</span></div>", unsafe_allow_html=True)
    if d or k:
        (st.success if d == k else st.warning)("Seimbang" if d == k else f"Belum seimbang, selisih Rp {rp(abs(d - k))}")
    if st.button(f"Simpan {nama.lower()}", type="primary", key=f"s_{jenis}"):
        baris = [(a.split()[0] if isinstance(a, str) and a else "", num(x), num(y)) for a, x, y in zip(df["Akun"], df["Debit"], df["Kredit"])]
        if jalankan(simpan_jurnal, jenis, prefix, tgl.strftime("%d-%m-%Y"), bukti, ket, baris):
            st.session_state.pop(f"df_{jenis}", None)
            st.session_state.pop(f"kt_{jenis}", None)
            st.session_state[f"v_{jenis}"] = v + 1
            pesan("ok", f"{nama} tersimpan dan sudah masuk ke buku besar.")
            st.rerun()


def halaman_input():
    form_input("JU", "JU", "Jurnal Umum")
