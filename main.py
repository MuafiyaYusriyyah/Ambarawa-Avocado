import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime

# 1. Inisialisasi Data & Daftar Akun
daftar_akun = [
    "101 - Kas",
    "102 - Piutang Usaha",
    "121 - Peralatan Kantor",
    "201 - Utang Usaha",
    "301 - Modal Pemilik",
    "401 - Pendapatan Jasa",
    "501 - Beban Sewa",
    "502 - Beban Gaji"
]

list_transaksi = []

# 2. Fungsi untuk Menambah Data ke Tabel
def tambah_transaksi():
    tanggal = entry_tanggal.get()
    akun_pilihan = combo_akun.get()
    posisi = combo_posisi.get()
    
    # Validasi nominal harus angka
    try:
        nominal = float(entry_nominal.get())
    except ValueError:
        messagebox.showerror("Error", "Nominal harus berupa angka!")
        return

    if not akun_pilihan:
        messagebox.showerror("Error", "Pilih akun terlebih dahulu!")
        return

    # Memisah kode ref dan nama akun
    ref, nama_akun = akun_pilihan.split(" - ")
    
    # Menentukan Debit atau Kredit
    debit = nominal if posisi == "Debit" else 0
    kredit = nominal if posisi == "Kredit" else 0
    
    # Format keterangan khusus kredit (menjorok ke dalam)
    keterangan_tabel = f"  {nama_akun}" if posisi == "Kredit" else nama_akun

    # Masukkan ke memori list
    list_transaksi.append({
        "Tanggal": tanggal,
        "Keterangan": keterangan_tabel,
        "Ref": ref,
        "Debit": debit,
        "Kredit": kredit
    })

    # Masukkan tampilan visual ke tabel GUI
    tabel_tampilan.insert("", "end", values=(tanggal, keterangan_tabel, ref, f"{debit:,.0f}", f"{kredit:,.0f}"))
    
    # Reset input nominal
    entry_nominal.delete(0, tk.END)

# 3. Fungsi Ekspor ke Excel
def ekspor_ke_excel():
    if not list_transaksi:
        messagebox.showwarning("Peringatan", "Belum ada data untuk diekspor!")
        return
        
    df = pd.DataFrame(list_transaksi)
    
    # Hitung total
    total_debit = df["Debit"].sum()
    total_kredit = df["Kredit"].sum()
    
    # Tambahkan baris total di paling bawah
    baris_total = pd.DataFrame([{"Tanggal": "TOTAL", "Keterangan": "", "Ref": "", "Debit": total_debit, "Kredit": total_kredit}])
    df_akhir = pd.concat([df, baris_total], ignore_index=True)
    
    # Simpan
    nama_file = "Jurnal_Umum_Otomatis.xlsx"
    df_akhir.to_excel(nama_file, index=False)
    messagebox.showinfo("Sukses", f"Data berhasil disimpan ke file:\n{nama_file}")

# 4. Membuat Window Utama GUI
root = tk.Tk()
root.title("Aplikasi Jurnal Umum Akuntansi")
root.geometry("650x550")

# --- FRAME INPUT ---
frame_input = tk.LabelFrame(root, text=" Input Transaksi ", padx=10, pady=10)
frame_input.pack(fill="x", padx=15, pady=10)

# Input Tanggal (Otomatis hari ini)
tk.Label(frame_input, text="Tanggal (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", pady=5)
entry_tanggal = tk.Entry(frame_input)
entry_tanggal.insert(0, datetime.today().strftime('%Y-%m-%d'))
entry_tanggal.grid(row=0, column=1, padx=5, pady=5)

# Dropdown Pilihan Akun
tk.Label(frame_input, text="Pilih Akun:").grid(row=1, column=0, sticky="w", pady=5)
combo_akun = ttk.Combobox(frame_input, values=daftar_akun, state="readonly", width=25)
combo_akun.grid(row=1, column=1, padx=5, pady=5)

# Dropdown Posisi (Debit/Kredit)
tk.Label(frame_input, text="Posisi:").grid(row=2, column=0, sticky="w", pady=5)
combo_posisi = ttk.Combobox(frame_input, values=["Debit", "Kredit"], state="readonly", width=10)
combo_posisi.current(0)
combo_posisi.grid(row=2, column=1, padx=5, pady=5, sticky="w")

# Input Nominal
tk.Label(frame_input, text="Nominal (Rp):").grid(row=3, column=0, sticky="w", pady=5)
entry_nominal = tk.Entry(frame_input)
entry_nominal.grid(row=3, column=1, padx=5, pady=5)

# Tombol Tambah
btn_tambah = tk.Button(frame_input, text="Tambah ke Jurnal", command=tambah_transaksi, bg="#4CAF50", fg="white")
btn_tambah.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")

# --- FRAME TABEL TAMPILAN ---
frame_tabel = tk.Frame(root)
frame_tabel.pack(fill="both", expand=True, padx=15, pady=5)

kolom = ("Tanggal", "Keterangan", "Ref", "Debit", "Kredit")
tabel_tampilan = ttk.Treeview(frame_tabel, columns=kolom, show="headings")
for col in kolom:
    tabel_tampilan.heading(col, text=col)
    tabel_tampilan.column(col, width=110, anchor="w" if col == "Keterangan" else "center")
tabel_tampilan.pack(fill="both", expand=True)
btn_ekspor = tk.Button(root, text="💾 Ekspor Semua ke Excel", command=ekspor_ke_excel, bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
btn_ekspor.pack(fill="x", padx=15, pady=15)
import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from openpyxl import load_workbook

FILE_NAME = "Jurnal_Umum_Otomatis.xlsx"

# Fungsi untuk memproses Buku Besar Otomatis dari data Jurnal Umum
def update_buku_besar():
    if not os.path.exists(FILE_NAME):
        return
        
    try:
        # 1. Baca data dari sheet Jurnal Umum
        df_jurnal = pd.read_excel(FILE_NAME, sheet_name="Jurnal Umum")
        
        # 2. Buka file excel dengan openpyxl untuk memanipulasi sheet lain tanpa menghapus Jurnal Umum
        book = load_workbook(FILE_NAME)
        
        # Dapatkan daftar semua akun unik yang ada di jurnal umum
        semua_akun = df_jurnal['Keterangan'].unique()
        
        for akun in semua_akun:
            # Filter data khusus untuk akun ini saja
            df_akun = df_jurnal[df_jurnal['Keterangan'] == akun].copy()
            
            # Hitung Saldo Kumulatif (Debit menambah, Kredit mengurangi)
            # Catatan: Ini asumsi saldo normal aset/beban. Anda bisa menyesuaikan logika ini jika diperlukan.
            saldo = 0
            daftar_saldo = []
            for _, row in df_akun.iterrows():
                saldo += row['Debit'] - row['Kredit']
                daftar_saldo.append(saldo)
            
            df_akun['Saldo'] = daftar_saldo
            
            # Bersihkan nama sheet dari karakter terlarang excel
            sheet_name = str(akun).replace("/", "-")[:30]
            
            # Jika sheet untuk akun tersebut sudah ada, hapus dulu agar bisa di-update dengan data terbaru
            if sheet_name in book.sheetnames:
                del book[sheet_name]
                
            # Buat sheet baru untuk akun ini
            book.create_sheet(title=sheet_name)
            sheet = book[sheet_name]
            
            # Tulis header tabel Buku Besar
            headers = ["Tanggal", "Keterangan", "Ref", "Debit", "Kredit", "Saldo"]
            sheet.append(headers)
            
            # Tulis baris data
            for _, row in df_akun[["Tanggal", "Keterangan", "Ref", "Debit", "Kredit", "Saldo"]].iterrows():
                sheet.append(row.tolist())
                
        # Simpan perubahan Buku Besar ke file excel
        book.save(FILE_NAME)
        book.close()
        
    except Exception as e:
        messagebox.showerror("Error Buku Besar", f"Gagal memperbarui Buku Besar: {e}")

# Fungsi saat tombol "Tambah ke Jurnal" diklik
def tambah_transaksi():
    tanggal = entry_tanggal.get()
    akun_info = combo_akun.get()  # Contoh: "101 - Kas"
    posisi = combo_posisi.get()
    
    try:
        nominal = float(entry_nominal.get())
    except ValueError:
        messagebox.showerror("Error", "Nominal harus berupa angka!")
        return

    if not tanggal or not akun_info or not posisi or nominal <= 0:
        messagebox.showerror("Error", "Semua data harus diisi dengan benar!")
        return

    # Pecah nomor akun dan nama akun
    parts = akun_info.split(" - ")
    ref = parts[0]
    keterangan = parts[1] if len(parts) > 1 else akun_info

    debit = nominal if posisi == "Debit" else 0
    kredit = nominal if posisi == "Kredit" else 0

    # Siapkan data baru
    data_baru = {
        "Tanggal": [tanggal],
        "Keterangan": [keterangan],
        "Ref": [int(ref)],
        "Debit": [debit],
        "Kredit": [kredit]
    }
    df_baru = pd.DataFrame(data_baru)

    # Simpan ke sheet Jurnal Umum
    if os.path.exists(FILE_NAME):
        try:
            with pd.ExcelWriter(FILE_NAME, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                # Cek apakah sheet Jurnal Umum sudah ada
                try:
                    df_lama = pd.read_excel(FILE_NAME, sheet_name="Jurnal Umum")
                    start_row = len(df_lama) + 1
                    df_baru.to_excel(writer, sheet_name="Jurnal Umum", startrow=start_row, index=False, header=False)
                except ValueError:
                    # Jika sheet belum ada sama sekali
                    df_baru.to_excel(writer, sheet_name="Jurnal Umum", index=False)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan ke Jurnal: {e}")
            return
    else:
        with pd.ExcelWriter(FILE_NAME, engine='openpyxl') as writer:
            df_baru.to_excel(writer, sheet_name="Jurnal Umum", index=False)

    # Tampilkan ke tabel UI (Treeview)
    tree.insert("", "end", values=(tanggal, keterangan, ref, f"{debit:,.0f}", f"{kredit:,.0f}"))
    
    # OTOMATISASI BUKU BESAR
    update_buku_besar()

    messagebox.showinfo("Sukses", f"Data berhasil disimpan ke Jurnal Umum & Buku Besar diperbarui di file:\n{FILE_NAME}")
    
    # Reset input nominal
    entry_nominal.delete(0, tk.END)

# --- DESAIN INTERFACE TKINTER ---
root = tk.Tk()
root.title("Aplikasi Akuntansi Otomatis")
root.geometry("600x550")

# 
frame_input = tk.LabelFrame(root, text="Input Transaksi", padx=10, pady=10)
frame_input.pack(padx=15, pady=10, fill="x")


tk.Label(frame_input, text="Tanggal (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", pady=5)
entry_tanggal = tk.Entry(frame_input)
entry_tanggal.insert(0, "2026-11-03")
entry_tanggal.grid(row=0, column=1, pady=5, sticky="ew")

tk.Label(frame_input, text="Pilih Akun:").grid(row=1, column=0, sticky="w", pady=5)
combo_akun = ttk.Combobox(frame_input, values=["101 - Kas", "502 - Beban Gaji", "401 - Pendapatan", "201 - Utang Usaha"])
combo_akun.grid(row=1, column=1, pady=5, sticky="ew")
combo_akun.current(0)

tk.Label(frame_input, text="Posisi:").grid(row=2, column=0, sticky="w", pady=5)
combo_posisi = ttk.Combobox(frame_input, values=["Debit", "Kredit"])
combo_posisi.grid(row=2, column=1, pady=5, sticky="ew")
combo_posisi.current(0)

tk.Label(frame_input, text="Nominal (Rp):").grid(row=3, column=0, sticky="w", pady=5)
entry_nominal = tk.Entry(frame_input)
entry_nominal.grid(row=3, column=1, pady=5, sticky="ew")

btn_tambah = tk.Button(frame_input, text="Tambah ke Jurnal & Buku Besar", bg="#4CAF50", fg="white", command=tambah_transaksi)
btn_tambah.grid(row=4, column=0, columnspan=2, pady=10, ipady=5, sticky="ew")

# Tabel UI Jurnal Umum
frame_tabel = tk.Frame(root)
frame_tabel.pack(padx=15, pady=5, fill="both", expand=True)

columns = ("tanggal", "keterangan", "ref", "debit", "kredit")
tree = ttk.Treeview(frame_tabel, columns=columns, show="headings")
tree.heading("tanggal", text="Tanggal")
tree.heading("keterangan", text="Keterangan")
tree.heading("ref", text="Ref")
tree.heading("debit", text="Debit")
tree.heading("kredit", text="Kredit")

tree.column("tanggal", width=100, anchor="center")
tree.column("keterangan", width=150)
tree.column("ref", width=50, anchor="center")
tree.column("debit", width=100, anchor="e")
tree.column("kredit", width=100, anchor="e")
tree.pack(fill="both", expand=True)

# Muat data awal jika file excel sudah ada
if os.path.exists(FILE_NAME):
    try:
        df_lama = pd.read_excel(FILE_NAME, sheet_name="Jurnal Umum")
        for _, row in df_lama.iterrows():
            tree.insert("", "end", values=(row['Tanggal'], row['Keterangan'], row['Ref'], f"{row['Debit']:,.0f}", f"{row['Kredit']:,.0f}"))
    except:
        pass

# 1. Daftar Akun Master (Kode, Nama, dan Saldo Normal)
master_akun = {
    "101": {"Nama": "Kas", "Normal": "Debit"},
    "102": {"Nama": "Piutang Usaha", "Normal": "Debit"},
    "121": {"Nama": "Peralatan Kantor", "Normal": "Debit"},
    "201": {"Nama": "Utang Usaha", "Normal": "Kredit"},
    "301": {"Nama": "Modal Pemilik", "Normal": "Kredit"},
    "401": {"Nama": "Pendapatan Jasa", "Normal": "Kredit"},
    "501": {"Nama": "Beban Sewa", "Normal": "Debit"},
    "502": {"Nama": "Beban Gaji", "Normal": "Debit"}
}

daftar_dropdown = [f"{k} - {v['Nama']}" for k, v in master_akun.items()]
list_transaksi = []

# 2. Fungsi Tambah Transaksi (Jurnal Umum)
def tambah_transaksi():
    tanggal = entry_tanggal.get()
    akun_pilihan = combo_akun.get()
    posisi = combo_posisi.get()
    
    try:
        nominal = float(entry_nominal.get())
    except ValueError:
        messagebox.showerror("Error", "Nominal harus berupa angka!")
        return

    if not akun_pilihan:
        messagebox.showerror("Error", "Pilih akun terlebih dahulu!")
        return

    ref = akun_pilihan.split(" - ")[0]
    nama_akun = master_akun[ref]["Nama"]
    
    debit = nominal if posisi == "Debit" else 0
    kredit = nominal if posisi == "Kredit" else 0
    keterangan_tabel = f"  {nama_akun}" if posisi == "Kredit" else nama_akun

    # Simpan ke memori
    list_transaksi.append({
        "Tanggal": tanggal, "Ref": ref, "Keterangan": keterangan_tabel, 
        "Debit": debit, "Kredit": kredit
    })

    # Tampilkan ke tabel GUI Jurnal Umum
    tabel_ju.insert("", "end", values=(tanggal, keterangan_tabel, ref, f"{debit:,.0f}", f"{kredit:,.0f}"))
    entry_nominal.delete(0, tk.END)

# --- FUNGSI BARU: HAPUS BARIS YANG DIPILIH ---
def hapus_transaksi():
    # Mengambil item/baris yang sedang diklik user di tabel
    selected_item = tabel_ju.selection()
    
    if not selected_item:
        messagebox.showwarning("Peringatan", "Pilih/klik baris tabel yang ingin dihapus terlebih dahulu!")
        return
        
    # Ambil indeks baris yang dipilih untuk menghapus dari memori list_transaksi
    index_terpilih = tabel_ju.index(selected_item)
    
    # Konfirmasi sebelum menghapus
    jawaban = messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin menghapus baris transaksi ini?")
    if jawaban:
        # 1. Hapus dari memori list
        list_transaksi.pop(index_terpilih)
        # 2. Hapus tampilan dari tabel GUI
        tabel_ju.delete(selected_item)
        messagebox.showinfo("Sukses", "Transaksi berhasil dihapus!")

# 3. Fungsi Pemrosesan Buku Besar & Neraca Lajur ke Excel
def ekspor_siklus_akuntansi():
    if not list_transaksi:
        messagebox.showwarning("Peringatan", "Belum ada transaksi yang diinput!")
        return
        
    df_ju = pd.DataFrame(list_transaksi)
    
    # --- A. PROSES BUKU BESAR (BB) ---
    bb_sheets = {}
    saldo_akhir_akun = {} # Mengingat saldo akhir untuk Neraca Lajur
    
    for ref, info in master_akun.items():
        df_filter = df_ju[df_ju["Ref"] == ref].copy()
        if not df_filter.empty:
            # Hitung Saldo Kumulatif
            saldo_list = []
            saldo_skrg = 0
            for _, row in df_filter.iterrows():
                if info["Normal"] == "Debit":
                    saldo_skrg += (row["Debit"] - row["Kredit"])
                else:
                    saldo_skrg += (row["Kredit"] - row["Debit"])
                saldo_list.append(saldo_skrg)
                
            df_filter["Saldo Kumulatif"] = saldo_list
            saldo_akhir_akun[ref] = saldo_skrg
        else:
            saldo_akhir_akun[ref] = 0
            
        bb_sheets[f"BB_{ref}"] = df_filter

    # --- B. PROSES NERACA LAJUR (NL) ---
    data_nl = []
    for ref, info in master_akun.items():
        saldo = saldo_akhir_akun.get(ref, 0)
        ns_debit = saldo if info["Normal"] == "Debit" else 0
        ns_kredit = saldo if info["Normal"] == "Kredit" else 0
        
        # Pemisahan Laba Rugi (Pendapatan & Beban: kepala 4 & 5)
        lr_debit = ns_debit if ref.startswith(("4", "5")) else 0
        lr_kredit = ns_kredit if ref.startswith(("4", "5")) else 0
        
        # Pemisahan Neraca (Aset, Kewajiban, Modal: kepala 1, 2, 3)
        n_debit = ns_debit if ref.startswith(("1", "2", "3")) else 0
        n_kredit = ns_kredit if ref.startswith(("1", "2", "3")) else 0
        
        data_nl.append({
            "Ref": ref, "Nama Akun": info["Nama"],
            "NS_Debit": ns_debit, "NS_Kredit": ns_kredit,
            "AJP_Debit": 0, "AJP_Kredit": 0, # Slot Penyesuaian kosong
            "NSSD_Debit": ns_debit, "NSSD_Kredit": ns_kredit,
            "LR_Debit": lr_debit, "LR_Kredit": lr_kredit,
            "N_Debit": n_debit, "N_Kredit": n_kredit
        })
        
    df_nl = pd.DataFrame(data_nl)
    
    # Tambah Baris Total Akhir Neraca Lajur
    total_row = {
        "Ref": "TOTAL", "Nama Akun": "",
        "NS_Debit": df_nl["NS_Debit"].sum(), "NS_Kredit": df_nl["NS_Kredit"].sum(),
        "AJP_Debit": 0, "AJP_Kredit": 0,
        "NSSD_Debit": df_nl["NSSD_Debit"].sum(), "NSSD_Kredit": df_nl["NSSD_Kredit"].sum(),
        "LR_Debit": df_nl["LR_Debit"].sum(), "LR_Kredit": df_nl["LR_Kredit"].sum(),
        "N_Debit": df_nl["N_Debit"].sum(), "N_Kredit": df_nl["N_Kredit"].sum()
    }
    df_nl = pd.concat([df_nl, pd.DataFrame([total_row])], ignore_index=True)

    # --- C. MENULIS SEMUA TABEL KE DALAM SATU FILE EXCEL (MULTI-SHEET) ---
    nama_file = "Siklus_Akuntansi_Lengkap.xlsx"
    with pd.ExcelWriter(nama_file, engine="openpyxl") as writer:
        # Sheet Jurnal Umum
        df_ju.to_excel(writer, sheet_name="Jurnal Umum", index=False)
        
        # Sheet Neraca Lajur
        df_nl.to_excel(writer, sheet_name="Neraca Lajur", index=False)
        
        # Sheet Buku Besar Terpisah berdasarkan Akun
        for sheet_name, df_bb in bb_sheets.items():
            if not df_bb.empty:
                df_bb.to_excel(writer, sheet_name=sheet_name, index=False)
                
    messagebox.showinfo("Sukses", f"Laporan Terintegrasi Berhasil Dibuat!\nFile: {nama_file}")

# 4. Pembuatan UI Aplikasi
root = tk.Tk()
root.title("Sistem Akuntansi Otomatis: JU, BB, Neraca Lajur")
root.geometry("700x600")

# Frame Input
frame_input = tk.LabelFrame(root, text=" Input Transaksi Baru ", padx=10, pady=10)
frame_input.pack(fill="x", padx=15, pady=10)

tk.Label(frame_input, text="Tanggal:").grid(row=0, column=0, sticky="w")
entry_tanggal = tk.Entry(frame_input)
entry_tanggal.insert(0, datetime.today().strftime('%Y-%m-%d'))
entry_tanggal.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame_input, text="Pilih Akun:").grid(row=1, column=0, sticky="w")
combo_akun = ttk.Combobox(frame_input, values=daftar_dropdown, state="readonly", width=25)
combo_akun.grid(row=1, column=1, padx=5, pady=5)

tk.Label(frame_input, text="Posisi:").grid(row=1, column=2, sticky="w")
combo_posisi = ttk.Combobox(frame_input, values=["Debit", "Kredit"], state="readonly", width=8)
combo_posisi.current(0)
combo_posisi.grid(row=1, column=3, padx=5, pady=5)

tk.Label(frame_input, text="Nominal:").grid(row=2, column=0, sticky="w")
entry_nominal = tk.Entry(frame_input)
entry_nominal.grid(row=2, column=1, padx=5, pady=5)

btn_tambah = tk.Button(frame_input, text="+ Masukkan Transaksi", command=tambah_transaksi, bg="#4CAF50", fg="white")
btn_tambah.grid(row=2, column=2, columnspan=2, padx=5, pady=5, sticky="ew")

# Frame Tabel Jurnal Umum Visual
frame_tabel = tk.LabelFrame(root, text=" Visualisasi Jurnal Umum ")
frame_tabel.pack(fill="both", expand=True, padx=15, pady=5)

kolom = ("Tanggal", "Keterangan", "Ref", "Debit", "Kredit")
tabel_ju = ttk.Treeview(frame_tabel, columns=kolom, show="headings")
for col in kolom:
    tabel_ju.heading(col, text=col)
    tabel_ju.column(col, width=120, anchor="w" if col == "Keterangan" else "center")
tabel_ju.pack(fill="both", expand=True, padx=5, pady=5)

# Tombol Proses Siklus Akhir
btn_proses = tk.Button(root, text="⚡ PROSES JURNAL -> BUKU BESAR -> NERACA LAJUR", 
                       command=ekspor_siklus_akuntansi, bg="#2196F3", fg="white", font=("Arial", 11, "bold"))
btn_proses.pack(fill="x", padx=15, pady=15)

# Menjalankan Aplikasi
root.mainloop()