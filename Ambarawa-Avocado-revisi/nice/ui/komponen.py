"""Komponen tampilan yang dipakai semua halaman: tabel, pesan, tombol hapus, dan pembantu kecil lainnya."""
import datetime as dt
import html

import pandas as pd
import streamlit as st

from core.util import D, Z, angka, rp, tgl

NAN = float("nan")


def num(x):
    """Isi sel / kolom angka -> Decimal (kosong dianggap 0)."""
    return angka(x) if x is not None and not pd.isna(x) else Z


def pesan(jenis, teks):
    """Simpan pesan untuk ditampilkan di halaman berikutnya (setelah st.rerun)."""
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
        st.error(f"{e}\n\nPeriksa koneksi MySQL (secrets atau core/config.py) dan pastikan database menyala.")
    return False


def bagian(teks, nomor=None):
    """Judul kecil untuk satu bagian halaman, dengan bulatan biji alpukat."""
    n = f"<span class='no'>{nomor}</span>" if nomor else "<span class='biji'></span>"
    st.markdown(f"<div class='bagian'>{n}{html.escape(teks)}</div>", unsafe_allow_html=True)


def fmt(sel, tag):
    """Sel tabel -> teks. Angka nol ditulis kosong, kecuali pada baris tebal (jumlah dan total)."""
    if isinstance(sel, dt.date):
        return tgl(sel)
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


def pilih_hapus(kunci, judul, daftar, label, aksi):
    """Kotak hapus: pilih satu baris dari daftar lalu hapus."""
    if not daftar:
        return
    with st.expander(judul):
        i = st.selectbox("Pilih", range(len(daftar)), format_func=lambda i: label(daftar[i]), key=f"sel_{kunci}")
        if st.button(judul, key=f"hps_{kunci}") and jalankan(aksi, daftar[i]):
            pesan("ok", "Data dihapus.")
            st.rerun()
