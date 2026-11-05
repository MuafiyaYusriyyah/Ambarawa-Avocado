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

# Menjalankan Aplikasi
root.mainloop()