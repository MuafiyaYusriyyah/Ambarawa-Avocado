"""Ekspor semua tabel ke satu file Excel. Buku besar = satu sheet untuk semua akun."""
import datetime as dt
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

import akuntansi as ak

SHEET = [("Penjualan", "jual"), ("Pembelian", "beli"), ("Jurnal Umum", "ju"), ("Buku Besar", "bb"), ("Neraca Saldo", "ns"), ("Jurnal Penyesuaian", "ajp"),
         ("BB Setelah Penyesuaian", "bb_ajp"), ("Neraca Lajur", "nl"), ("Laba Rugi", "lr"), ("Perubahan Ekuitas", "ek"),
         ("Posisi Keuangan", "pos"), ("Jurnal Penutup", "pnt"), ("Neraca Saldo Akhir", "nsa"),
         ("Kartu Stok Segar", "k104"), ("Kartu Stok Frozen", "k105")]


def buat_excel(path):
    """path boleh nama file atau objek file (BytesIO)."""
    b = ak.Buku()
    wb = Workbook()
    wb.remove(wb.active)
    for nama, kunci in SHEET:
        kolom, rows = ak.TABEL[kunci](b)
        ws = wb.create_sheet(nama)
        ws.append([k[0] for k in kolom])
        for i, k in enumerate(kolom):
            ws.column_dimensions[chr(65 + i)].width = k[1] / 7
        for sel in ws[1]:
            sel.font, sel.fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="2F5D3A")
        for isi, tag, *_ in rows:
            ws.append([float(x) if isinstance(x, Decimal) else x for x in isi])
            for sel in ws[ws.max_row]:
                if isinstance(sel.value, float):
                    sel.number_format = '#,##0;(#,##0);"-"'
                elif isinstance(sel.value, dt.date):
                    sel.number_format = "DD-MM-YYYY"
                if tag == "b":
                    sel.font = Font(bold=True)
    wb.save(path)
