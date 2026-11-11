"""Ambarawa Avocado - Siklus Akuntansi (Streamlit + MySQL).   Jalankan: streamlit run app.py

File ini hanya menyusun menu dan memanggil halaman. Isi tiap tahap siklus ada di foldernya sendiri:
    siklus/transaksi.py            input Penerimaan, Pengeluaran, Transaksi Lainnya (pintu masuk, otomatis menjadi jurnal)
    siklus/saldo_awal.py           0. saldo awal
    siklus/ju.py                   1. jurnal umum
    siklus/persediaan.py           kartu stok alpukat
    siklus/bukbes.py               2. buku besar
    siklus/neraca_saldo.py         3. neraca saldo
    siklus/ajp.py                  4. jurnal penyesuaian
    siklus/bukbes_ajp.py           5. buku besar setelah penyesuaian
    siklus/neraca_lajur.py         6. neraca lajur
    siklus/laporan.py              7. laporan keuangan
    siklus/jurnal_penutup.py       8. jurnal penutup
    siklus/neraca_saldo_akhir.py   9. neraca saldo akhir
    siklus/daftar_akun.py          daftar akun (tambah dan hapus)
"""
import io

import streamlit as st

from core import db
from siklus import (ajp, bukbes, bukbes_ajp, daftar_akun, ekspor, jurnal_penutup, ju, neraca_lajur, neraca_saldo,
                    neraca_saldo_akhir, persediaan, saldo_awal, transaksi, laporan)
from ui import beranda, login, tema
from ui.komponen import buka

st.set_page_config(page_title="Ambarawa Avocado", page_icon="🥑", layout="wide")
tema.terapkan()

HALAMAN = {
    "beranda": ("Beranda", beranda.halaman), "akun": ("Daftar Akun", daftar_akun.halaman), "saldo_awal": ("Saldo Awal", saldo_awal.halaman),
    "terima": ("Penerimaan", lambda: transaksi.halaman("TERIMA")), "keluar": ("Pengeluaran", lambda: transaksi.halaman("KELUAR")),
    "lain": ("Transaksi Lainnya", lambda: transaksi.halaman("LAIN")),
    "ju": ("Jurnal Umum", ju.halaman), "persediaan": ("Persediaan", persediaan.halaman), "bb": ("Buku Besar", bukbes.halaman),
    "ns": ("Neraca Saldo", neraca_saldo.halaman), "ajp": ("Jurnal Penyesuaian", ajp.halaman),
    "bb_ajp": ("Buku Besar Setelah Penyesuaian", bukbes_ajp.halaman), "nl": ("Neraca Lajur", neraca_lajur.halaman),
    "lap": ("Laporan Keuangan", laporan.halaman), "pnt": ("Jurnal Penutup", jurnal_penutup.halaman),
    "nsa": ("Neraca Saldo Akhir", neraca_saldo_akhir.halaman),
    "in_saldo": ("Input Saldo Awal", saldo_awal.halaman_input), "in_ju": ("Input Jurnal Umum Manual", ju.halaman_input),
    "in_ajp": ("Input Jurnal Penyesuaian", ajp.halaman_input),
}
MENU = [("Persiapan", [("beranda", "Beranda"), ("akun", "Daftar Akun"), ("saldo_awal", "0. Saldo Awal")]),
        ("Input Transaksi", [("terima", "Penerimaan"), ("keluar", "Pengeluaran"), ("lain", "Transaksi Lainnya")]),
        ("Siklus Akuntansi", [("ju", "1. Jurnal Umum"), ("persediaan", "Persediaan"), ("bb", "2. Buku Besar"), ("ns", "3. Neraca Saldo"),
                              ("ajp", "4. Jurnal Penyesuaian"), ("bb_ajp", "5. Buku Besar Setelah Penyesuaian"), ("nl", "6. Neraca Lajur"),
                              ("lap", "7. Laporan Keuangan"), ("pnt", "8. Jurnal Penutup"), ("nsa", "9. Neraca Saldo Akhir")])]


@st.cache_resource(show_spinner=False)
def siap():
    db.siapkan_database()
    return True


def main():
    login.gerbang()
    try:
        siap()
    except Exception as e:
        st.error(f"Tidak bisa terhubung ke MySQL: {e}")
        st.info("Periksa .streamlit/secrets.toml (atau core/config.py) dan pastikan MySQL menyala.")
        st.stop()
    hal = st.session_state.setdefault("hal", "beranda")
    aktif = "beranda" if hal.startswith("in_") else hal
    with st.sidebar:
        st.markdown("<div class='merek'>" + tema.alpukat_svg(34) + "<div><b>Ambarawa Avocado</b><small>Sistem Akuntansi</small></div></div>", unsafe_allow_html=True)
        for judul, items in MENU:
            st.caption(judul.upper())
            for k, teks in items:
                st.button(teks, key=f"m_{k}", on_click=buka, args=(k,), type="primary" if k == aktif else "secondary")
        st.caption("EKSPOR")
        if st.button("Siapkan file Excel", key="m_xlsx"):
            buf = io.BytesIO()
            ekspor.buat_excel(buf)
            st.session_state["xlsx"] = buf.getvalue()
        if "xlsx" in st.session_state:
            st.download_button("Unduh Excel", st.session_state["xlsx"], "Siklus_Akuntansi_Ambarawa_Avocado.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        login.tombol_keluar()
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
