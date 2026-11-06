import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

class AkuntansiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Siklus Akuntansi Harian Terpusat - Ambarawa Avocado")
        self.root.geometry("980x750")
        self.root.configure(bg="#F4F6F9")

        # Database SQLite untuk Penyimpanan Transaksi Harian
        self.db_name = "akuntansi_harian.db"
        self.init_db()

        # Master Akun Ambarawa Avocado
        self.accounts = [
            {"Kode": "1-101", "Nama": "Kas", "Tipe": "Aset", "Normal": "Debit"},
            {"Kode": "1-102", "Nama": "Bank BRI", "Tipe": "Aset", "Normal": "Debit"},
            {"Kode": "1-103", "Nama": "Piutang Usaha", "Tipe": "Aset", "Normal": "Debit"},
            {"Kode": "1-104", "Nama": "Persediaan Alpukat Segar", "Tipe": "Aset", "Normal": "Debit"},
            {"Kode": "1-105", "Nama": "Persediaan Alpukat Frozen", "Tipe": "Aset", "Normal": "Debit"},
            {"Kode": "1-106", "Nama": "Peralatan Usaha", "Tipe": "Aset", "Normal": "Debit"},
            {"Kode": "1-107", "Nama": "Peralatan Pengolahan Frozen", "Tipe": "Aset", "Normal": "Debit"},
            {"Kode": "1-108", "Nama": "Akumulasi Penyusutan Peralatan", "Tipe": "Aset", "Normal": "Kredit"},
            {"Kode": "2-101", "Nama": "Utang Usaha", "Tipe": "Liabilitas", "Normal": "Kredit"},
            {"Kode": "2-102", "Nama": "Utang Gaji", "Tipe": "Liabilitas", "Normal": "Kredit"},
            {"Kode": "3-101", "Nama": "Modal Pemilik", "Tipe": "Ekuitas", "Normal": "Kredit"},
            {"Kode": "3-102", "Nama": "Prive", "Tipe": "Ekuitas", "Normal": "Debit"},
            {"Kode": "4-101", "Nama": "Penjualan Alpukat Segar", "Tipe": "Pendapatan", "Normal": "Kredit"},
            {"Kode": "4-102", "Nama": "Penjualan Alpukat Frozen", "Tipe": "Pendapatan", "Normal": "Kredit"},
            {"Kode": "4-103", "Nama": "Penjualan Alpukat untuk Jus", "Tipe": "Pendapatan", "Normal": "Kredit"},
            {"Kode": "4-104", "Nama": "Pendapatan Lain-lain", "Tipe": "Pendapatan", "Normal": "Kredit"},
            {"Kode": "4-105", "Nama": "Retur Penjualan", "Tipe": "Pendapatan", "Normal": "Debit"},
            {"Kode": "4-106", "Nama": "Potongan Penjualan", "Tipe": "Pendapatan", "Normal": "Debit"},
            {"Kode": "5-101", "Nama": "Pembelian Alpukat Segar", "Tipe": "Pembelian", "Normal": "Debit"},
            {"Kode": "5-102", "Nama": "Retur Pembelian", "Tipe": "Pembelian", "Normal": "Kredit"},
            {"Kode": "5-103", "Nama": "Potongan Pembelian", "Tipe": "Pembelian", "Normal": "Kredit"},
            {"Kode": "6-101", "Nama": "HPP Alpukat Segar", "Tipe": "HPP", "Normal": "Debit"},
            {"Kode": "6-102", "Nama": "HPP Alpukat Frozen", "Tipe": "HPP", "Normal": "Debit"},
            {"Kode": "6-103", "Nama": "HPP Alpukat untuk Jus", "Tipe": "HPP", "Normal": "Debit"},
            {"Kode": "7-101", "Nama": "Beban Gaji", "Tipe": "Beban", "Normal": "Debit"},
            {"Kode": "7-102", "Nama": "Beban Perawatan Tanaman", "Tipe": "Beban", "Normal": "Debit"},
            {"Kode": "7-103", "Nama": "Beban Produksi Frozen", "Tipe": "Beban", "Normal": "Debit"},
            {"Kode": "7-104", "Nama": "Beban Pengiriman", "Tipe": "Beban", "Normal": "Debit"},
            {"Kode": "7-105", "Nama": "Beban Penyusutan", "Tipe": "Beban", "Normal": "Debit"},
            {"Kode": "7-106", "Nama": "Beban Perlengkapan", "Tipe": "Beban", "Normal": "Debit"},
            {"Kode": "7-107", "Nama": "Beban Kompensasi Kerusakan Barang", "Tipe": "Beban", "Normal": "Debit"},
            {"Kode": "7-108", "Nama": "Beban Operasional Lainnya", "Tipe": "Beban", "Normal": "Debit"},
            {"Kode": "9-999", "Nama": "Ikhtisar Laba Rugi", "Tipe": "Nominal", "Normal": "Kredit"},
        ]

        # ------------------- HEADER GUI -------------------
        header_frame = tk.Frame(self.root, bg="#1F4E78", pady=12)
        header_frame.pack(fill=tk.X)
        
        lbl_title = tk.Label(header_frame, text="Siklus Akuntansi Harian (Terpusat) - Ambarawa Avocado", font=("Segoe UI", 16, "bold"), fg="white", bg="#1F4E78")
        lbl_title.pack()

        # ------------------- TAB SYSTEM -------------------
        self.tabControl = ttk.Notebook(self.root)
        self.tab1 = ttk.Frame(self.tabControl)
        self.tab2 = ttk.Frame(self.tabControl)

        self.tabControl.add(self.tab1, text="Input Jurnal Umum Harian")
        self.tabControl.add(self.tab2, text="Input Jurnal Penyesuaian (AJP)")
        self.tabControl.pack(expand=1, fill="both", padx=10, pady=10)

        # Build UI Tabs
        self.build_ju_tab()
        self.build_ajp_tab()

        # Muat Data dari DB ke Tabel GUI
        self.refresh_table_ju()
        self.refresh_table_ajp()

        # ------------------- BOTTOM CONTAINER -------------------
        bottom_frame = tk.Frame(self.root, bg="#F4F6F9", pady=10)
        bottom_frame.pack(fill=tk.X)

        btn_excel = tk.Button(
            bottom_frame, 
            text=" Export Laporan Keuangan Lengkap ke Excel ", 
            font=("Segoe UI", 11, "bold"), 
            bg="#2F5597", 
            fg="white", 
            padx=20, 
            pady=8, 
            bd=0, 
            cursor="hand2",
            command=self.proses_akuntansi
        )
        btn_excel.pack()

    # ------------------- DATABASE HANDLING -------------------
    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jurnal_umum (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tanggal TEXT,
                akun TEXT,
                ref TEXT,
                debit REAL,
                kredit REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ajp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tanggal TEXT,
                akun TEXT,
                ref TEXT,
                debit REAL,
                kredit REAL
            )
        ''')
        conn.commit()
        conn.close()

    # ------------------- TAB JURNAL UMUM -------------------
    def build_ju_tab(self):
        input_frame = tk.LabelFrame(self.tab1, text=" Tambah Transaksi Harian JU ", font=("Segoe UI", 10, "bold"), padx=15, pady=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(input_frame, text="Tanggal (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_tgl_ju = tk.Entry(input_frame, width=15)
        self.ent_tgl_ju.insert(0, "2026-12-01")
        self.ent_tgl_ju.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Nama Akun:").grid(row=0, column=2, sticky="w", pady=5)
        akun_options = [f"{a['Kode']} - {a['Nama']}" for a in self.accounts if a["Kode"] != "9-999"]
        self.combo_akun_ju = ttk.Combobox(input_frame, values=akun_options, width=35, state="readonly")
        self.combo_akun_ju.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(input_frame, text="Debit (Rp):").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_debit_ju = tk.Entry(input_frame, width=15)
        self.ent_debit_ju.insert(0, "0")
        self.ent_debit_ju.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Kredit (Rp):").grid(row=1, column=2, sticky="w", pady=5)
        self.ent_kredit_ju = tk.Entry(input_frame, width=15)
        self.ent_kredit_ju.insert(0, "0")
        self.ent_kredit_ju.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        btn_add = tk.Button(input_frame, text="+ Simpan Transaksi JU", bg="#27AE60", fg="white", font=("Segoe UI", 9, "bold"), command=self.tambah_ju)
        btn_add.grid(row=1, column=4, padx=10, pady=5)

        table_frame = tk.Frame(self.tab1)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("ID", "Tanggal", "Nama Akun", "Ref", "Debit", "Kredit")
        self.tree_ju = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree_ju.heading(col, text=col)
            self.tree_ju.column(col, anchor="center" if col in ["ID", "Tanggal", "Ref"] else "w" if col == "Nama Akun" else "e")
        self.tree_ju.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        btn_del = tk.Button(self.tab1, text="Hapus Baris Terpilih dari Database", bg="#C0392B", fg="white", command=self.hapus_ju)
        btn_del.pack(anchor="e", padx=10, pady=5)

    def tambah_ju(self):
        tgl = self.ent_tgl_ju.get()
        selected_acc = self.combo_akun_ju.get()
        deb_str = self.ent_debit_ju.get().strip()
        kre_str = self.ent_kredit_ju.get().strip()

        try:
            debit = float(deb_str) if deb_str != "" else 0.0
            kredit = float(kre_str) if kre_str != "" else 0.0
        except ValueError:
            messagebox.showerror("Error", "Debit dan Kredit harus berupa angka!")
            return

        if not selected_acc:
            messagebox.showwarning("Peringatan", "Pilih akun terlebih dahulu!")
            return

        ref, nama_akun = selected_acc.split(" - ", 1)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO jurnal_umum (tanggal, akun, ref, debit, kredit) VALUES (?, ?, ?, ?, ?)",
                       (tgl, nama_akun, ref, debit, kredit))
        conn.commit()
        conn.close()

        self.refresh_table_ju()
        self.ent_debit_ju.delete(0, tk.END); self.ent_debit_ju.insert(0, "0")
        self.ent_kredit_ju.delete(0, tk.END); self.ent_kredit_ju.insert(0, "0")

    def refresh_table_ju(self):
        for item in self.tree_ju.get_children():
            self.tree_ju.delete(item)
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, tanggal, akun, ref, debit, kredit FROM jurnal_umum ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            self.tree_ju.insert("", "end", values=(row[0], row[1], row[2], row[3], f"{row[4]:,.0f}", f"{row[5]:,.0f}"))

    def hapus_ju(self):
        selected_item = self.tree_ju.selection()
        if not selected_item: return
        item_vals = self.tree_ju.item(selected_item[0])['values']
        row_id = item_vals[0]

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jurnal_umum WHERE id = ?", (row_id,))
        conn.commit()
        conn.close()
        self.refresh_table_ju()

    # ------------------- TAB AJP -------------------
    def build_ajp_tab(self):
        input_frame = tk.LabelFrame(self.tab2, text=" Tambah Jurnal Penyesuaian (AJP) ", font=("Segoe UI", 10, "bold"), padx=15, pady=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(input_frame, text="Tanggal (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_tgl_ajp = tk.Entry(input_frame, width=15)
        self.ent_tgl_ajp.insert(0, "2026-12-31")
        self.ent_tgl_ajp.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Nama Akun:").grid(row=0, column=2, sticky="w", pady=5)
        akun_options = [f"{a['Kode']} - {a['Nama']}" for a in self.accounts]
        self.combo_akun_ajp = ttk.Combobox(input_frame, values=akun_options, width=35, state="readonly")
        self.combo_akun_ajp.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(input_frame, text="Debit (Rp):").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_debit_ajp = tk.Entry(input_frame, width=15)
        self.ent_debit_ajp.insert(0, "0")
        self.ent_debit_ajp.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Kredit (Rp):").grid(row=1, column=2, sticky="w", pady=5)
        self.ent_kredit_ajp = tk.Entry(input_frame, width=15)
        self.ent_kredit_ajp.insert(0, "0")
        self.ent_kredit_ajp.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        btn_add = tk.Button(input_frame, text="+ Simpan Transaksi AJP", bg="#27AE60", fg="white", font=("Segoe UI", 9, "bold"), command=self.tambah_ajp)
        btn_add.grid(row=1, column=4, padx=10, pady=5)

        table_frame = tk.Frame(self.tab2)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("ID", "Tanggal", "Nama Akun", "Ref", "Debit", "Kredit")
        self.tree_ajp = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree_ajp.heading(col, text=col)
            self.tree_ajp.column(col, anchor="center" if col in ["ID", "Tanggal", "Ref"] else "w" if col == "Nama Akun" else "e")
        self.tree_ajp.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        btn_del = tk.Button(self.tab2, text="Hapus Baris Terpilih dari Database", bg="#C0392B", fg="white", command=self.hapus_ajp)
        btn_del.pack(anchor="e", padx=10, pady=5)

    def tambah_ajp(self):
        tgl = self.ent_tgl_ajp.get()
        selected_acc = self.combo_akun_ajp.get()
        deb_str = self.ent_debit_ajp.get().strip()
        kre_str = self.ent_kredit_ajp.get().strip()

        try:
            debit = float(deb_str) if deb_str != "" else 0.0
            kredit = float(kre_str) if kre_str != "" else 0.0
        except ValueError:
            messagebox.showerror("Error", "Debit dan Kredit harus berupa angka!")
            return

        if not selected_acc:
            messagebox.showwarning("Peringatan", "Pilih akun terlebih dahulu!")
            return

        ref, nama_akun = selected_acc.split(" - ", 1)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ajp (tanggal, akun, ref, debit, kredit) VALUES (?, ?, ?, ?, ?)",
                       (tgl, nama_akun, ref, debit, kredit))
        conn.commit()
        conn.close()

        self.refresh_table_ajp()
        self.ent_debit_ajp.delete(0, tk.END); self.ent_debit_ajp.insert(0, "0")
        self.ent_kredit_ajp.delete(0, tk.END); self.ent_kredit_ajp.insert(0, "0")

    def refresh_table_ajp(self):
        for item in self.tree_ajp.get_children():
            self.tree_ajp.delete(item)
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, tanggal, akun, ref, debit, kredit FROM ajp ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            self.tree_ajp.insert("", "end", values=(row[0], row[1], row[2], row[3], f"{row[4]:,.0f}", f"{row[5]:,.0f}"))

    def hapus_ajp(self):
        selected_item = self.tree_ajp.selection()
        if not selected_item: return
        item_vals = self.tree_ajp.item(selected_item[0])['values']
        row_id = item_vals[0]

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ajp WHERE id = ?", (row_id,))
        conn.commit()
        conn.close()
        self.refresh_table_ajp()

    # ------------------- PROSES EXPORT AKUNTANSI -------------------
    def proses_akuntansi(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT tanggal, akun, ref, debit, kredit FROM jurnal_umum")
        ju_list = [{"Tanggal": r[0], "Akun": r[1], "Ref": r[2], "Debit": r[3], "Kredit": r[4]} for r in cursor.fetchall()]

        cursor.execute("SELECT tanggal, akun, ref, debit, kredit FROM ajp")
        ajp_list = [{"Tanggal": r[0], "Akun": r[1], "Ref": r[2], "Debit": r[3], "Kredit": r[4]} for r in cursor.fetchall()]
        conn.close()

        if not ju_list:
            messagebox.showwarning("Peringatan", "Belum ada transaksi di database!")
            return

        tot_d = sum(x["Debit"] for x in ju_list)
        tot_k = sum(x["Kredit"] for x in ju_list)
        if tot_d != tot_k:
            messagebox.showerror("Jurnal Tidak Balance", f"Total Debit ({tot_d:,.0f}) dan Kredit ({tot_k:,.0f}) Jurnal Umum tidak seimbang!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            title="Export Laporan Keuangan Lengkap",
            initialfile="Laporan_Keuangan_Ambarawa_Avocado.xlsx"
        )
        if not file_path: return

        try:
            self.generate_excel(file_path, ju_list, ajp_list)
            messagebox.showinfo("Berhasil!", f"Laporan Akuntansi Berhasil Di-export!\nFile tersimpan di:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan saat mengeksport Excel:\n{str(e)}")

    def generate_excel(self, file_path, ju_list, ajp_list):
        wb = openpyxl.Workbook()
        wb.remove(wb.active)

        font_title = Font(name="Calibri", size=14, bold=True, color="1F4E78")
        font_subtitle = Font(name="Calibri", size=11, bold=True, color="595959")
        font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        font_bold = Font(name="Calibri", size=10, bold=True)
        font_normal = Font(name="Calibri", size=10)

        fill_header = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        fill_sub = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
        fill_total = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        fill_selisih = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

        thin = Side(style='thin', color='D9D9D9')
        double = Side(style='double', color='000000')
        top_line = Side(style='thin', color='000000')

        border_data = Border(left=thin, right=thin, top=thin, bottom=thin)
        border_total = Border(top=top_line, bottom=double)

        def header_perusahaan(ws, judul_laporan):
            ws.append(["AMBARAWA AVOCADO"])
            ws.append([judul_laporan.upper()])
            ws.append(["Periode Berakhir 31 Desember 2026"])
            ws.append([])
            ws.cell(row=1, column=1).font = font_title
            ws.cell(row=2, column=1).font = font_subtitle
            ws.cell(row=3, column=1).font = font_subtitle

        # SHEET 1: JURNAL UMUM
        ws_ju = wb.create_sheet(title="Jurnal Umum")
        header_perusahaan(ws_ju, "Jurnal Umum")
        ws_ju.append(["Tanggal", "Nama Akun", "Ref", "Debit (Rp)", "Kredit (Rp)"])
        for cell in ws_ju[5]: cell.font, cell.fill, cell.alignment = font_header, fill_header, Alignment(horizontal="center")
        for item in ju_list: ws_ju.append([item["Tanggal"], item["Akun"], item["Ref"], item["Debit"], item["Kredit"]])
        tot_ju_row = len(ju_list) + 6
        ws_ju.append(["TOTAL", "", "", f"=SUM(D6:D{tot_ju_row-1})", f"=SUM(E6:E{tot_ju_row-1})"])
        for r in range(6, tot_ju_row + 1):
            for c in range(1, 6):
                cell = ws_ju.cell(row=r, column=c)
                cell.font = font_bold if r == tot_ju_row else font_normal
                cell.border = border_total if r == tot_ju_row else border_data
                if c in [4, 5]: cell.number_format = '#,##0'

        # SHEET 2: BUKU BESAR
        ws_bb = wb.create_sheet(title="Buku Besar")
        header_perusahaan(ws_bb, "Buku Besar (Gabungan)")
        curr_r = 5
        for acc in self.accounts:
            txs_ju = [t for t in ju_list if t["Ref"] == acc["Kode"]]
            txs_ajp = [t for t in ajp_list if t["Ref"] == acc["Kode"]]
            if not txs_ju and not txs_ajp: continue
            
            ws_bb.cell(row=curr_r, column=1, value=f"Nama Akun: {acc['Nama']}").font = font_bold
            ws_bb.cell(row=curr_r, column=5, value=f"Kode: {acc['Kode']}").font = font_bold
            curr_r += 1
            headers = ["Tanggal", "Keterangan", "Debit", "Kredit", "Saldo Debit", "Saldo Kredit"]
            for col_idx, h in enumerate(headers, start=1):
                c = ws_bb.cell(row=curr_r, column=col_idx, value=h)
                c.font, c.fill, c.alignment = font_header, fill_sub, Alignment(horizontal="center")
            curr_r += 1
            s_d, s_k = 0, 0
            for t in txs_ju:
                if acc["Normal"] == "Debit": s_d += (t["Debit"] - t["Kredit"])
                else: s_k += (t["Kredit"] - t["Debit"])
                ws_bb.append([t["Tanggal"], "Posting JU", t["Debit"], t["Kredit"], s_d if acc["Normal"]=="Debit" else 0, s_k if acc["Normal"]=="Kredit" else 0])
                curr_r += 1
                for col in range(1, 7):
                    cell = ws_bb.cell(row=curr_r-1, column=col)
                    cell.font, cell.border = font_normal, border_data
                    if col >= 3: cell.number_format = '#,##0'
            for t in txs_ajp:
                if acc["Normal"] == "Debit": s_d += (t["Debit"] - t["Kredit"])
                else: s_k += (t["Kredit"] - t["Debit"])
                ws_bb.append([t["Tanggal"], "Posting AJP", t["Debit"], t["Kredit"], s_d if acc["Normal"]=="Debit" else 0, s_k if acc["Normal"]=="Kredit" else 0])
                curr_r += 1
                for col in range(1, 7):
                    cell = ws_bb.cell(row=curr_r-1, column=col)
                    cell.font, cell.border = font_normal, border_data
                    if col >= 3: cell.number_format = '#,##0'
            curr_r += 1

        # SHEET 3: NERACA SALDO
        ws_ns = wb.create_sheet(title="Neraca Saldo")
        header_perusahaan(ws_ns, "Neraca Saldo")
        ws_ns.append(["Kode Akun", "Nama Akun", "Debit (Rp)", "Kredit (Rp)"])
        for cell in ws_ns[5]: cell.font, cell.fill, cell.alignment = font_header, fill_header, Alignment(horizontal="center")
        ns_count = 0
        for acc in self.accounts:
            txs = [t for t in ju_list if t["Ref"] == acc["Kode"]]
            d_val, k_val = sum(t["Debit"] for t in txs), sum(t["Kredit"] for t in txs)
            s_d = max(0, d_val - k_val) if acc["Normal"] == "Debit" else 0
            s_k = max(0, k_val - d_val) if acc["Normal"] == "Kredit" else 0
            if s_d > 0 or s_k > 0:
                ws_ns.append([acc["Kode"], acc["Nama"], s_d, s_k])
                ns_count += 1
        tot_ns_r = ns_count + 6
        ws_ns.append(["TOTAL", "", f"=SUM(C6:C{tot_ns_r-1})", f"=SUM(D6:D{tot_ns_r-1})"])
        for r in range(6, tot_ns_r + 1):
            for c in range(1, 5):
                cell = ws_ns.cell(row=r, column=c)
                cell.font = font_bold if r == tot_ns_r else font_normal
                cell.border = border_total if r == tot_ns_r else border_data
                if c in [3, 4]: cell.number_format = '#,##0'

        # SHEET 4: JURNAL PENYESUAIAN
        ws_ajp = wb.create_sheet(title="Jurnal Penyesuai & BB")
        header_perusahaan(ws_ajp, "Jurnal Penyesuaian")
        ws_ajp.append(["Tanggal", "Nama Akun", "Ref", "Debit (Rp)", "Kredit (Rp)"])
        for cell in ws_ajp[5]: cell.font, cell.fill = font_header, fill_header
        for item in ajp_list: ws_ajp.append([item["Tanggal"], item["Akun"], item["Ref"], item["Debit"], item["Kredit"]])
        tot_ajp_r = len(ajp_list) + 6
        ws_ajp.append(["TOTAL", "", "", f"=SUM(D6:D{tot_ajp_r-1})", f"=SUM(E6:E{tot_ajp_r-1})"])
        for r in range(6, tot_ajp_r + 1):
            for c in range(1, 6):
                cell = ws_ajp.cell(row=r, column=c)
                cell.font = font_bold if r == tot_ajp_r else font_normal
                cell.border = border_total if r == tot_ajp_r else border_data
                if c in [4, 5]: cell.number_format = '#,##0'

        # SHEET 5: NERACA LAJUR (10 KOLOM)
        ws_nl = wb.create_sheet(title="Neraca Lajur")
        header_perusahaan(ws_nl, "Neraca Lajur (Worksheet)")
        ws_nl.append(["Kode", "Nama Akun", "Neraca Saldo", "", "Penyesuaian", "", "NS Disesuaikan", "", "Laba Rugi", "", "Neraca", ""])
        ws_nl.append(["", "", "Debit", "Kredit", "Debit", "Kredit", "Debit", "Kredit", "Debit", "Kredit", "Debit", "Kredit"])
        ws_nl.merge_cells("A5:A6"); ws_nl.merge_cells("B5:B6")
        ws_nl.merge_cells("C5:D5"); ws_nl.merge_cells("E5:F5")
        ws_nl.merge_cells("G5:H5"); ws_nl.merge_cells("I5:J5"); ws_nl.merge_cells("K5:L5")
        for r in range(5, 7):
            for c in range(1, 13):
                cell = ws_nl.cell(row=r, column=c)
                cell.font, cell.fill, cell.alignment = font_header, fill_header, Alignment(horizontal="center", vertical="center")

        start_r = 7
        for idx, acc in enumerate(self.accounts, start=start_r):
            r = idx
            ns_d = sum(t["Debit"] for t in ju_list if t["Ref"] == acc["Kode"])
            ns_k = sum(t["Kredit"] for t in ju_list if t["Ref"] == acc["Kode"])
            s_ns_d = max(0, ns_d - ns_k) if acc["Normal"] == "Debit" else 0
            s_ns_k = max(0, ns_k - ns_d) if acc["Normal"] == "Kredit" else 0
            ajp_d = sum(t["Debit"] for t in ajp_list if t["Ref"] == acc["Kode"])
            ajp_k = sum(t["Kredit"] for t in ajp_list if t["Ref"] == acc["Kode"])

            ws_nl.append([
                acc["Kode"], acc["Nama"], s_ns_d, s_ns_k, ajp_d, ajp_k,
                f"=IF((C{r}+E{r}-D{r}-F{r})>0, C{r}+E{r}-D{r}-F{r}, 0)",
                f"=IF((D{r}+F{r}-C{r}-E{r})>0, D{r}+F{r}-C{r}-E{r}, 0)",
                f'=IF(OR(LEFT(A{r},1)="4",LEFT(A{r},1)="5",LEFT(A{r},1)="6",LEFT(A{r},1)="7"), G{r}, 0)',
                f'=IF(OR(LEFT(A{r},1)="4",LEFT(A{r},1)="5",LEFT(A{r},1)="6",LEFT(A{r},1)="7"), H{r}, 0)',
                f'=IF(AND(LEFT(A{r},1)<>"4",LEFT(A{r},1)<>"5",LEFT(A{r},1)<>"6",LEFT(A{r},1)<>"7"), G{r}, 0)',
                f'=IF(AND(LEFT(A{r},1)<>"4",LEFT(A{r},1)<>"5",LEFT(A{r},1)<>"6",LEFT(A{r},1)<>"7"), H{r}, 0)'
            ])

        end_r = start_r + len(self.accounts) - 1
        r_tot = end_r + 1
        ws_nl.append([
            "TOTAL", "",
            f"=SUM(C{start_r}:C{end_r})", f"=SUM(D{start_r}:D{end_r})",
            f"=SUM(E{start_r}:E{end_r})", f"=SUM(F{start_r}:F{end_r})",
            f"=SUM(G{start_r}:G{end_r})", f"=SUM(H{start_r}:H{end_r})",
            f"=SUM(I{start_r}:I{end_r})", f"=SUM(J{start_r}:J{end_r})",
            f"=SUM(K{start_r}:K{end_r})", f"=SUM(L{start_r}:L{end_r})"
        ])

        r_sel = r_tot + 1
        f_lr_d = f"=IF(J{r_tot}>I{r_tot}, J{r_tot}-I{r_tot}, 0)"
        f_lr_k = f"=IF(I{r_tot}>J{r_tot}, I{r_tot}-J{r_tot}, 0)"
        f_nrc_d = f"=IF(I{r_tot}>J{r_tot}, I{r_tot}-J{r_tot}, 0)"
        f_nrc_k = f"=IF(J{r_tot}>I{r_tot}, J{r_tot}-I{r_tot}, 0)"
        ws_nl.append(["LABA / (RUGI) BERSIH", "", "", "", "", "", "", "", f_lr_d, f_lr_k, f_nrc_d, f_nrc_k])

        r_bal = r_sel + 1
        ws_nl.append([
            "TOTAL SEIMBANG", "",
            f"=C{r_tot}", f"=D{r_tot}", f"=E{r_tot}", f"=F{r_tot}", f"=G{r_tot}", f"=H{r_tot}",
            f"=SUM(I{r_tot}:I{r_sel})", f"=SUM(J{r_tot}:J{r_sel})", f"=SUM(K{r_tot}:K{r_sel})", f"=SUM(L{r_tot}:L{r_sel})"
        ])

        for r in range(start_r, r_bal + 1):
            for c in range(1, 13):
                cell = ws_nl.cell(row=r, column=c)
                if r <= end_r: cell.font, cell.border = font_normal, border_data
                elif r == r_tot: cell.font, cell.fill, cell.border = font_bold, fill_total, border_data
                elif r == r_sel: cell.font, cell.fill, cell.border = font_bold, fill_selisih, border_data
                elif r == r_bal: cell.font, cell.fill, cell.border = font_bold, fill_total, border_total
                if c >= 3: cell.number_format = '#,##0'

        # SHEET 6: LAPORAN KEUANGAN
        ws_lk = wb.create_sheet(title="Laporan Keuangan")
        header_perusahaan(ws_lk, "Laporan Keuangan Lengkap")
        
        row_idx = 5
        ws_lk.cell(row=row_idx, column=1, value="1. LAPORAN LABA RUGI").font = font_title
        row_idx += 1
        ws_lk.cell(row=row_idx, column=1, value="Pendapatan Operasional:").font = font_bold
        row_idx += 1
        
        start_pdp = row_idx
        for a in self.accounts:
            if a["Kode"].startswith("4"):
                ws_lk.append([f"   {a['Nama']}", f"='Neraca Lajur'!H{self.accounts.index(a)+7} - 'Neraca Lajur'!G{self.accounts.index(a)+7}"])
                row_idx += 1

        end_pdp = row_idx - 1
        tot_pdp_row = row_idx
        ws_lk.append(["Total Pendapatan", f"=SUM(B{start_pdp}:B{end_pdp})"])
        ws_lk.cell(row=tot_pdp_row, column=1).font = font_bold
        ws_lk.cell(row=tot_pdp_row, column=2).font = font_bold
        row_idx += 2

        ws_lk.cell(row=row_idx, column=1, value="Beban Operasional & HPP:").font = font_bold
        row_idx += 1
        start_bbn = row_idx
        for a in self.accounts:
            if a["Kode"].startswith("5") or a["Kode"].startswith("6") or a["Kode"].startswith("7"):
                ws_lk.append([f"   {a['Nama']}", f"='Neraca Lajur'!G{self.accounts.index(a)+7} - 'Neraca Lajur'!H{self.accounts.index(a)+7}"])
                row_idx += 1

        end_bbn = row_idx - 1
        tot_bbn_row = row_idx
        ws_lk.append(["Total Beban & HPP", f"=SUM(B{start_bbn}:B{end_bbn})"])
        ws_lk.cell(row=tot_bbn_row, column=1).font = font_bold
        ws_lk.cell(row=tot_bbn_row, column=2).font = font_bold
        row_idx += 1

        laba_row = row_idx
        ws_lk.append(["LABA (RUGI) BERSIH", f"=B{tot_pdp_row}-B{tot_bbn_row}"])
        ws_lk.cell(row=laba_row, column=1).font = font_bold
        ws_lk.cell(row=laba_row, column=2).font = font_bold
        ws_lk.cell(row=laba_row, column=1).fill = fill_selisih
        ws_lk.cell(row=laba_row, column=2).fill = fill_selisih
        row_idx += 3

        ws_lk.cell(row=row_idx, column=1, value="2. LAPORAN PERUBAHAN EKUITAS").font = font_title
        row_idx += 1
        mod_awal_row = row_idx
        ws_lk.append(["Modal Awal Pemilik", "='Neraca Lajur'!L17"])
        row_idx += 1
        laba_ekuitas_row = row_idx
        ws_lk.append(["Laba (Rugi) Bersih Periode Berjalan", f"=B{laba_row}"])
        row_idx += 1
        prive_row = row_idx
        ws_lk.append(["Pengambilan Pribadi (Prive)", "='Neraca Lajur'!K18"])
        row_idx += 1
        mod_akhir_row = row_idx
        ws_lk.append(["MODAL AKHIR PEMILIK", f"=B{mod_awal_row}+B{laba_ekuitas_row}-B{prive_row}"])
        ws_lk.cell(row=mod_akhir_row, column=1).font = font_bold
        ws_lk.cell(row=mod_akhir_row, column=2).font = font_bold
        row_idx += 3

        ws_lk.cell(row=row_idx, column=1, value="3. LAPORAN POSISI KEUANGAN (NERACA)").font = font_title
        row_idx += 1
        ws_lk.cell(row=row_idx, column=1, value="ASET").font = font_bold
        row_idx += 1
        start_aset = row_idx
        for a in self.accounts:
            if a["Kode"].startswith("1"):
                ws_lk.append([f"   {a['Nama']}", f"='Neraca Lajur'!K{self.accounts.index(a)+7} - 'Neraca Lajur'!L{self.accounts.index(a)+7}"])
                row_idx += 1
        end_aset = row_idx - 1
        tot_aset_row = row_idx
        ws_lk.append(["TOTAL ASET", f"=SUM(B{start_aset}:B{end_aset})"])
        ws_lk.cell(row=tot_aset_row, column=1).font = font_bold
        ws_lk.cell(row=tot_aset_row, column=2).font = font_bold
        row_idx += 2

        ws_lk.cell(row=row_idx, column=1, value="LIABILITAS DAN EKUITAS").font = font_bold
        row_idx += 1
        start_liab = row_idx
        for a in self.accounts:
            if a["Kode"].startswith("2"):
                ws_lk.append([f"   {a['Nama']}", f"='Neraca Lajur'!L{self.accounts.index(a)+7} - 'Neraca Lajur'!K{self.accounts.index(a)+7}"])
                row_idx += 1
        end_liab = row_idx - 1
        tot_liab_row = row_idx
        ws_lk.append(["Total Liabilitas", f"=SUM(B{start_liab}:B{end_liab})"])
        ws_lk.cell(row=tot_liab_row, column=1).font = font_bold
        ws_lk.cell(row=tot_liab_row, column=2).font = font_bold
        row_idx += 1

        mod_posisi_row = row_idx
        ws_lk.append(["   Modal Akhir Pemilik", f"=B{mod_akhir_row}"])
        row_idx += 1

        tot_pasiva_row = row_idx
        ws_lk.append(["TOTAL LIABILITAS DAN EKUITAS", f"=B{tot_liab_row}+B{mod_posisi_row}"])
        ws_lk.cell(row=tot_pasiva_row, column=1).font = font_bold
        ws_lk.cell(row=tot_pasiva_row, column=2).font = font_bold
        
        for r in range(5, row_idx + 1):
            cell_val = ws_lk.cell(row=r, column=2)
            if cell_val.value is not None:
                cell_val.number_format = '#,##0'

        # SHEET 7: JURNAL PENUTUP
        ws_jp = wb.create_sheet(title="Jurnal Penutup")
        header_perusahaan(ws_jp, "Jurnal Penutup")
        ws_jp.append(["Tanggal", "Nama Akun", "Ref", "Debit (Rp)", "Kredit (Rp)"])
        for cell in ws_jp[5]: cell.font, cell.fill = font_header, fill_header

        jp_data = [
            {"Tanggal": "2026-12-31", "Akun": "Penjualan Alpukat Segar", "Ref": "4-101", "Debit": f"='Neraca Lajur'!J19", "Kredit": 0},
            {"Tanggal": "2026-12-31", "Akun": "Penjualan Alpukat Frozen", "Ref": "4-102", "Debit": f"='Neraca Lajur'!J20", "Kredit": 0},
            {"Tanggal": "2026-12-31", "Akun": "Ikhtisar Laba Rugi", "Ref": "9-999", "Debit": 0, "Kredit": "=D6+D7"},
            {"Tanggal": "2026-12-31", "Akun": "Ikhtisar Laba Rugi", "Ref": "9-999", "Debit": "=E10+E11+E12+E13+E14", "Kredit": 0},
            {"Tanggal": "2026-12-31", "Akun": "Beban Gaji", "Ref": "7-101", "Debit": 0, "Kredit": f"='Neraca Lajur'!I31"},
            {"Tanggal": "2026-12-31", "Akun": "Beban Penyusutan", "Ref": "7-105", "Debit": 0, "Kredit": f"='Neraca Lajur'!I35"},
            {"Tanggal": "2026-12-31", "Akun": "Ikhtisar Laba Rugi", "Ref": "9-999", "Debit": f"='Laporan Keuangan'!B17", "Kredit": 0},
            {"Tanggal": "2026-12-31", "Akun": "Modal Pemilik", "Ref": "3-101", "Debit": 0, "Kredit": f"='Laporan Keuangan'!B17"},
            {"Tanggal": "2026-12-31", "Akun": "Modal Pemilik", "Ref": "3-101", "Debit": f"='Neraca Lajur'!K18", "Kredit": 0},
            {"Tanggal": "2026-12-31", "Akun": "Prive", "Ref": "3-102", "Debit": 0, "Kredit": f"='Neraca Lajur'!K18"},
        ]
        for item in jp_data: ws_jp.append([item["Tanggal"], item["Akun"], item["Ref"], item["Debit"], item["Kredit"]])
        tot_jp_r = len(jp_data) + 6
        ws_jp.append(["TOTAL", "", "", f"=SUM(D6:D{tot_jp_r-1})", f"=SUM(E6:E{tot_jp_r-1})"])
        for r in range(6, tot_jp_r + 1):
            for c in range(1, 6):
                cell = ws_jp.cell(row=r, column=c)
                cell.font = font_bold if r == tot_jp_r else font_normal
                cell.border = border_total if r == tot_jp_r else border_data
                if c in [4, 5]: cell.number_format = '#,##0'

        # SHEET 8: NERACA SALDO SETELAH PENUTUPAN
        ws_nsp = wb.create_sheet(title="NS Setelah Penutupan")
        header_perusahaan(ws_nsp, "Neraca Saldo Setelah Penutupan")
        ws_nsp.append(["Kode Akun", "Nama Akun", "Debit (Rp)", "Kredit (Rp)"])
        for cell in ws_nsp[5]: cell.font, cell.fill, cell.alignment = font_header, fill_header, Alignment(horizontal="center")

        start_nsp = 6
        count_nsp = 0
        for idx, a in enumerate(self.accounts, start=7):
            if a["Kode"].startswith("1") or a["Kode"].startswith("2"):
                ws_nsp.append([a["Kode"], a["Nama"], f"='Neraca Lajur'!K{idx}", f"='Neraca Lajur'!L{idx}"])
                count_nsp += 1
            elif a["Kode"] == "3-101":
                ws_nsp.append([a["Kode"], a["Nama"], 0, f"='Laporan Keuangan'!B{mod_akhir_row}"])
                count_nsp += 1

        end_nsp = start_nsp + count_nsp - 1
        tot_nsp_r = end_nsp + 1
        ws_nsp.append(["TOTAL", "", f"=SUM(C{start_nsp}:C{end_nsp})", f"=SUM(D{start_nsp}:D{end_nsp})"])

        for r in range(6, tot_nsp_r + 1):
            for c in range(1, 5):
                cell = ws_nsp.cell(row=r, column=c)
                cell.font = font_bold if r == tot_nsp_r else font_normal
                cell.border = border_total if r == tot_nsp_r else border_data
                if c in [3, 4]: cell.number_format = '#,##0'

        for sheet in wb.worksheets:
            for col in sheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = get_column_letter(col[0].column)
                sheet.column_dimensions[col_letter].width = max(max_len + 3, 15)

        wb.save(file_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = AkuntansiApp(root)
    root.mainloop()