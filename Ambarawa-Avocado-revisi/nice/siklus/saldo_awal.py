"""TAHAP 0 - SALDO AWAL.
Saldo awal akun aset, liabilitas, dan modal. Untuk akun persediaan isi juga jumlahnya dalam kg."""
import pandas as pd
import streamlit as st

from core.buku import Buku
from core.db import ambil, cursor
from core.konstanta import STOK
from core.util import B, Z, angka, dec, kol, rp
from ui.komponen import jalankan, num, pesan, tampil

KOL_AWAL = kol(("Kode", 90, "w"), ("Nama Akun", 380, "w"), ("Debit", 170, "e"), ("Kredit", 170, "e"), ("Jumlah (kg)", 110, "e"))


def akun_awal():
    return ambil("SELECT a.kode,a.nama,a.saldo_normal,s.debit,s.kredit,s.qty FROM akun a LEFT JOIN saldo_awal s ON s.kode=a.kode "
                 "WHERE a.kelompok IN ('Aset','Liabilitas') OR a.kode='3-101' ORDER BY a.kode")


def simpan(isian):
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


def tabel(b):
    rows, td, tk = [], Z, Z
    for a in b.akun:
        d, k, q = b.sa.get(a["kode"], (Z, Z, Z))
        if d or k:
            rows.append(B(a["kode"], a["nama"], d, k, q if a["kode"] in STOK else None))
            td, tk = td + d, tk + k
    return KOL_AWAL, (rows or [B("", "Saldo awal belum diisi.", tag="kosong")]) + [B("", "TOTAL", td, tk, None, tag="b")]


def halaman():
    tampil(*tabel(Buku()))


def halaman_input():
    akun = akun_awal()
    df = pd.DataFrame([{"Kode": a["kode"], "Nama Akun": a["nama"], "Sisi": "Debit" if a["saldo_normal"] == "D" else "Kredit",
                        "Saldo (Rp)": float(dec(a["debit"] if a["saldo_normal"] == "D" else a["kredit"])),
                        "Jumlah (kg)": float(dec(a["qty"]))} for a in akun])
    ed = st.data_editor(df, hide_index=True, key="ed_awal", disabled=["Kode", "Nama Akun", "Sisi"],
                        column_config={"Saldo (Rp)": st.column_config.NumberColumn(min_value=0, step=1000),
                                       "Jumlah (kg)": st.column_config.NumberColumn(min_value=0, help="Isi hanya untuk akun persediaan")})
    isian, d, k = {}, Z, Z
    for a, (_, r) in zip(akun, ed.iterrows()):
        v = num(r["Saldo (Rp)"])
        isian[a["kode"]] = (v, num(r["Jumlah (kg)"]) if a["kode"] in STOK else Z)
        d, k = (d + v, k) if a["saldo_normal"] == "D" else (d, k + v)
    st.markdown(f"<div class='total-box'>Debit <span>Rp {rp(d, '0')}</span> &nbsp;·&nbsp; Kredit <span>Rp {rp(k, '0')}</span> &nbsp;·&nbsp; Selisih <span>Rp {rp(d - k, '0')}</span></div>", unsafe_allow_html=True)
    if st.button("Simpan saldo awal", type="primary") and jalankan(simpan, isian):
        pesan("ok" if d == k else "peringatan", "Saldo awal tersimpan." + ("" if d == k else " Namun total debit dan kredit belum seimbang."))
        st.rerun()
