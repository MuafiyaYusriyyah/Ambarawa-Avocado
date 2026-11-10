"""Ekspor seluruh siklus akuntansi ke satu file Excel (buku besar = 1 sheet untuk semua akun)."""
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side

import akuntansi as ak

HIJAU = PatternFill("solid", fgColor="2D4A2B")
LIME = PatternFill("solid", fgColor="E3EBB8")
KRIM = PatternFill("solid", fgColor="F7F2DE")
PUTIH = Font(bold=True, color="FFFFFF")
TEBAL = Font(bold=True)
ATAS = Border(top=Side(style="thin", color="2D4A2B"))
FMT = '#,##0;(#,##0);"-"'


def _lembar(wb, nama, judul, sub, header, lebar):
    ws = wb.create_sheet(nama)
    ws["A1"], ws["A2"] = "AMBARAWA AVOCADO", judul
    ws["A3"] = sub
    ws["A1"].font, ws["A2"].font, ws["A3"].font = Font(bold=True, size=14, color="2D4A2B"), Font(bold=True, size=12), Font(italic=True)
    for i, w in enumerate(lebar, 1):
        ws.column_dimensions[chr(64 + i)].width = w
    if header:
        ws.append([])
        ws.append(header)
        for c in ws[ws.max_row]:
            c.fill, c.font, c.alignment = HIJAU, PUTIH, Alignment(horizontal="center", wrap_text=True)
    return ws


def _baris(ws, nilai, tebal=False, isi=None):
    ws.append(nilai)
    for c in ws[ws.max_row]:
        if isinstance(c.value, (int, float)) or hasattr(c.value, "as_tuple"):
            c.number_format = FMT
        if tebal:
            c.font, c.border = TEBAL, ATAS
        if isi:
            c.fill = isi


def _jurnal(wb, nama, judul, jenis, sub):
    daftar, td, tk = ak.daftar_jurnal(jenis)
    ws = _lembar(wb, nama, judul, sub, ["Tanggal", "Bukti", "Keterangan / Akun", "Ref", "Debit", "Kredit"], [13, 12, 46, 9, 16, 16])
    for j in daftar:
        _baris(ws, [j["tanggal"].strftime("%d-%m-%Y"), j["bukti"], j["ket"], "", None, None], isi=KRIM)
        for r in j["baris"]:
            _baris(ws, ["", "", ("      " if r["k"] else "") + r["nama"], r["kode"], r["d"] or None, r["k"] or None])
    _baris(ws, ["", "", "TOTAL " + judul.upper(), "", td, tk], tebal=True, isi=LIME)


def _saldo(wb, nama, judul, sub, rows, td, tk):
    ws = _lembar(wb, nama, judul, sub, ["Kode", "Nama Akun", "Debit", "Kredit"], [10, 40, 18, 18])
    for r in rows:
        _baris(ws, [r["kode"], r["nama"], r["d"] or None, r["k"] or None])
    _baris(ws, ["", "TOTAL", td, tk], tebal=True, isi=LIME)


def _buku_besar(wb, nama, judul, sub, data):
    ws = _lembar(wb, nama, judul, sub, None, [13, 40, 12, 16, 16, 18])
    for g in data:
        ws.append([])
        _baris(ws, [f"{g['kode']}  {g['nama']}", "", "", "", "", "Saldo normal: " + ("Debit" if g["normal"] == "D" else "Kredit")], tebal=True, isi=LIME)
        ws.append(["Tanggal", "Keterangan", "Bukti", "Debit", "Kredit", "Saldo"])
        for c in ws[ws.max_row]:
            c.fill, c.font = HIJAU, PUTIH
        for r in g["baris"]:
            _baris(ws, [r["tgl"].strftime("%d-%m-%Y") if r["tgl"] else "", r["ket"], r["bukti"], r["d"] or None, r["k"] or None, r["saldo"]])
        _baris(ws, ["", "Jumlah", "", g["td"], g["tk"], g["saldo"]], tebal=True)


def buat_excel(b):
    wb = Workbook()
    wb.remove(wb.active)
    pr = b.pg["nama_periode"] if b.pg else ""
    _jurnal(wb, "Jurnal Umum", "Jurnal Umum", "JU", pr)
    _buku_besar(wb, "Buku Besar", "Buku Besar", pr, b.buku_besar(("JU",)))
    rows, td, tk = b.neraca_saldo()
    _saldo(wb, "Neraca Saldo", "Neraca Saldo", pr, rows, td, tk)
    _jurnal(wb, "Jurnal Penyesuaian", "Jurnal Penyesuaian", "AJP", pr)
    _buku_besar(wb, "Buku Besar Penyesuaian", "Buku Besar Setelah Penyesuaian", pr, b.buku_besar(("JU", "AJP")))

    nl = b.neraca_lajur()
    ws = _lembar(wb, "Neraca Lajur", "Neraca Lajur", pr, None, [10, 32] + [14] * 10)
    ws.append([])
    ws.append(["Kode", "Nama Akun", "Neraca Saldo", "", "Penyesuaian", "", "Saldo Disesuaikan", "", "Laba Rugi", "", "Neraca", ""])
    ws.append(["", ""] + ["Debit", "Kredit"] * 5)
    for rr in (ws.max_row - 1, ws.max_row):
        for c in ws[rr]:
            c.fill, c.font, c.alignment = HIJAU, PUTIH, Alignment(horizontal="center")
    ks = ["ns_d", "ns_k", "aj_d", "aj_k", "na_d", "na_k", "lr_d", "lr_k", "nr_d", "nr_k"]
    for r in nl["rows"]:
        _baris(ws, [r["kode"], r["nama"]] + [r[k] or None for k in ks])
    _baris(ws, ["", "JUMLAH"] + [nl["tot"][k] for k in ks], tebal=True, isi=KRIM)
    _baris(ws, ["", f"SELISIH ({nl['status'].upper()} BERSIH)"] + [nl["sel"][k] or None for k in ks], tebal=True, isi=LIME)
    _baris(ws, ["", "JUMLAH SEIMBANG"] + [nl["akhir"][k] for k in ks], tebal=True, isi=KRIM)

    lap = b.laporan()
    lr, ek, pos = lap["lr"], lap["ek"], lap["pos"]
    ws = _lembar(wb, "Laba Rugi", "Laporan Laba Rugi", pr, None, [46, 18, 18])
    ws.append([])
    ws.append(["Pendapatan"]); ws[ws.max_row][0].font = TEBAL
    for r in lr["pend"]:
        _baris(ws, ["   " + r["nama"], r["jml"], None])
    for r in lr["poto"]:
        _baris(ws, ["   (-) " + r["nama"], -r["jml"], None])
    _baris(ws, ["Penjualan Bersih", None, lr["penjualan_bersih"]], tebal=True)
    ws.append(["Harga Pokok Penjualan"]); ws[ws.max_row][0].font = TEBAL
    for r in lr["beli"]:
        _baris(ws, ["   " + r["nama"], r["jml"] if r["normal"] == "D" else -r["jml"], None])
    for r in lr["hpp"]:
        _baris(ws, ["   " + r["nama"], r["jml"], None])
    _baris(ws, ["Total Harga Pokok Penjualan", None, lr["total_hpp"]], tebal=True)
    _baris(ws, ["LABA KOTOR", None, lr["laba_kotor"]], tebal=True, isi=KRIM)
    ws.append(["Beban Operasional"]); ws[ws.max_row][0].font = TEBAL
    for r in lr["beban"]:
        _baris(ws, ["   " + r["nama"], r["jml"], None])
    _baris(ws, ["Total Beban Operasional", None, lr["total_beban"]], tebal=True)
    _baris(ws, ["LABA USAHA", None, lr["laba_usaha"]], tebal=True, isi=KRIM)
    for r in lr["lain"]:
        _baris(ws, [r["nama"], None, r["jml"]])
    _baris(ws, ["LABA (RUGI) BERSIH", None, lr["laba"]], tebal=True, isi=LIME)

    ws = _lembar(wb, "Perubahan Ekuitas", "Laporan Perubahan Ekuitas", pr, None, [46, 18])
    ws.append([])
    for n, v in [("Modal Pemilik Awal", ek["modal_awal"]), ("Penambahan Modal", ek["tambahan"]),
                 ("Laba (Rugi) Bersih", ek["laba"]), ("Prive", -ek["prive"])]:
        _baris(ws, [n, v])
    _baris(ws, ["MODAL PEMILIK AKHIR", ek["modal_akhir"]], tebal=True, isi=LIME)

    ws = _lembar(wb, "Posisi Keuangan", "Laporan Posisi Keuangan", pr, None, [46, 18, 18])
    ws.append([])
    ws.append(["ASET"]); ws[ws.max_row][0].font = TEBAL
    for r in pos["lancar"]:
        _baris(ws, ["   " + r["nama"], r["jml"], None])
    _baris(ws, ["Total Aset Lancar", None, pos["total_lancar"]], tebal=True)
    for r in pos["tetap"]:
        _baris(ws, ["   " + r["nama"], r["jml"], None])
    _baris(ws, ["Total Aset Tetap", None, pos["total_tetap"]], tebal=True)
    _baris(ws, ["TOTAL ASET", None, pos["total_aset"]], tebal=True, isi=LIME)
    ws.append(["LIABILITAS"]); ws[ws.max_row][0].font = TEBAL
    for r in pos["liab"]:
        _baris(ws, ["   " + r["nama"], r["jml"], None])
    _baris(ws, ["Total Liabilitas", None, pos["total_liab"]], tebal=True)
    _baris(ws, ["EKUITAS - Modal Pemilik", None, pos["modal_akhir"]], tebal=True)
    _baris(ws, ["TOTAL LIABILITAS + EKUITAS", None, pos["total_pasiva"]], tebal=True, isi=LIME)

    ent, td, tk = b.penutup()
    ws = _lembar(wb, "Jurnal Penutup", "Jurnal Penutup", pr, ["Tanggal", "Keterangan / Akun", "Ref", "Debit", "Kredit"], [13, 56, 9, 16, 16])
    for e in ent:
        _baris(ws, [e["tanggal"].strftime("%d-%m-%Y") if e["tanggal"] else "", e["ket"], "", None, None], isi=KRIM)
        for r in e["baris"]:
            _baris(ws, ["", ("      " if r["k"] else "") + r["nama"], r["kode"], r["d"] or None, r["k"] or None])
    _baris(ws, ["", "TOTAL JURNAL PENUTUP", "", td, tk], tebal=True, isi=LIME)

    rows, td, tk = b.saldo_akhir()
    _saldo(wb, "Neraca Saldo Akhir", "Neraca Saldo Akhir", pr, rows, td, tk)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
