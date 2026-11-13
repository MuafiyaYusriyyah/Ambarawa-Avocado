"""TAHAP 4 - JURNAL PENYESUAIAN.
Memakai tabel dan form yang sama dengan jurnal umum (ju.py), hanya jenisnya AJP.
Tombol Isi cepat membantu menyusun penyesuaian yang umum."""
from siklus import ju

# (teks tombol, keterangan, akun debit, akun kredit)
CEPAT = [("Penyusutan peralatan", "Penyusutan peralatan periode ini", "7-105", "1-108"),
         ("Gaji terutang", "Gaji pekerja yang masih terutang", "7-101", "2-102")]


def tabel(b):
    return ju.tabel_jenis("AJP")


def halaman():
    ju.halaman_jenis("AJP")


def halaman_input():
    ju.form_input("AJP", "AJP", "Jurnal Penyesuaian", CEPAT)

    
