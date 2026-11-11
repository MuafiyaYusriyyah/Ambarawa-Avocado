"""EKSPOR - semua tabel siklus ke satu file Excel. Buku besar = satu sheet untuk semua akun."""
import datetime as dt
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from core.buku import Buku
from siklus import (ajp, bukbes, bukbes_ajp, jurnal_penutup, ju, laporan, neraca_lajur, neraca_saldo, neraca_saldo_akhir,
                    persediaan, transaksi)

# (nama sheet, fungsi yang menerima Buku dan mengembalikan (kolom, baris))
SHEET = [("Penerimaan", transaksi.tabel_terima), ("Pengeluaran", transaksi.tabel_keluar), ("Transaksi Lainnya", transaksi.tabel_lain),
         ("Jurnal Umum", ju.tabel), ("Buku Besar", bukbes.tabel), ("Neraca Saldo", neraca_saldo.tabel), ("Jurnal Penyesuaian", ajp.tabel),
         ("BB Setelah Penyesuaian", bukbes_ajp.tabel), ("Neraca Lajur", neraca_lajur.tabel), ("Laba Rugi", laporan.laba_rugi),
         ("Perubahan Ekuitas", laporan.ekuitas), ("Posisi Keuangan", laporan.posisi), ("Jurnal Penutup", jurnal_penutup.tabel),
         ("Neraca Saldo Akhir", neraca_saldo_akhir.tabel), ("Kartu Stok Segar", persediaan.tabel_segar), ("Kartu Stok Frozen", persediaan.tabel_frozen)]


def buat_excel(path):
    """path boleh nama file atau objek file (BytesIO)."""
    b = Buku()
    wb = Workbook()
    wb.remove(wb.active)
    for nama, fungsi in SHEET:
        kolom, rows = fungsi(b)
        ws = wb.create_sheet(nama)
        ws.append([k[0] for k in kolom])
        for i, k in enumerate(kolom):
            ws.column_dimensions[chr(65 + i)].width = k[1] / 7
        for sel in ws[1]:
            sel.font, sel.fill = Font(bold=True, color="1F3D28"), PatternFill("solid", fgColor="C9DF93")
        for isi, tag, *_ in rows:
            ws.append([float(x) if isinstance(x, Decimal) else x for x in isi])
            for sel in ws[ws.max_row]:
                if isinstance(sel.value, float):
                    sel.number_format = '#,##0;(#,##0);"-"'
                elif isinstance(sel.value, dt.date):
                    sel.number_format = "DD-MM-YYYY"
                if tag == "b":
                    sel.font = Font(bold=True, color="6A4125")
    wb.save(path)
