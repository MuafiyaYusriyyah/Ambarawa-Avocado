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
# Menjalankan Aplikasi
root.mainloop()