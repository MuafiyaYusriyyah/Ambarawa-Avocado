import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
from datetime import datetime

# 1. DAFTAR AKUN MASTER (Kode, Nama Akun, dan Saldo Normal)
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
nama_file = "Siklus_Akuntansi_Lengkap.xlsx"

# 2. FUNGSI UPDATE BARIS TOTAL DI LAYAR GUI secara REAL-TIME
def update_total_di_layar():
    for item in tabel_ju.get_children():
        values = tabel_ju.item(item, "values")
        if values and values[0] == "TOTAL":
            tabel_ju.delete(item)
            
    total_debit = sum(float(x["Debit"]) for x in list_transaksi)
    total_kredit = sum(float(x["Kredit"]) for x in list_transaksi)
    tabel_ju.insert("", "end", values=("TOTAL", "", "", f"{total_debit:,.0f}", f"{total_kredit:,.0f}"))

# 3. FUNGSI MEMBACA DATA LAMA DARI EXCEL SAAT APLIKASI DIBUKA
def muat_data_dari_excel():
    global list_transaksi
    if os.path.exists(nama_file):
        try:
            df_lama = pd.read_excel(nama_file, sheet_name="Jurnal Umum")
            df_lama = df_lama[df_lama["Tanggal"] != "TOTAL"].copy()
            df_lama["Ref"] = df_lama["Ref"].astype(str)
            list_transaksi = df_lama.to_dict(orient="records")
            
            for row in list_transaksi:
                tabel_ju.insert("", "end", values=(
                    row["Tanggal"], row["Keterangan"], row["Ref"], 
                    f"{row['Debit']:,.0f}", f"{row['Kredit']:,.0f}"
                ))
            update_total_di_layar()
        except Exception as e:
            print(f"Gagal memuat data lama: {e}")

# 4. FUNGSI TAMBAH TRANSAKSI BARU VIA GUI
def tambah_transaksi():
    tanggal = entry_tanggal.get()
    akun_pilihan = combo_akun.get()
    posisi = combo_posisi.get()
    
    teks_nominal = entry_nominal.get().replace(".", "").replace(",", "")
    try:
        nominal = float(teks_nominal)
    except ValueError:
        messagebox.showerror("Error", "Nominal harus berupa angka polos!")
        return

    if not akun_pilihan:
        messagebox.showerror("Error", "Pilih akun terlebih dahulu!")
        return

    ref = akun_pilihan.split(" - ")[0]
    nama_akun = master_akun[ref]["Nama"]
    
    debit = nominal if posisi == "Debit" else 0
    kredit = nominal if posisi == "Kredit" else 0
    keterangan_tabel = f"  {nama_akun}" if posisi == "Kredit" else nama_akun

    list_transaksi.append({
        "Tanggal": tanggal, "Ref": ref, "Keterangan": keterangan_tabel, 
        "Debit": debit, "Kredit": kredit
    })

    tabel_ju.insert("", "end", values=(tanggal, keterangan_tabel, ref, f"{debit:,.0f}", f"{kredit:,.0f}"))
    update_total_di_layar()
    entry_nominal.delete(0, tk.END)

# 5. FUNGSI HAPUS BARIS YANG SALAH INPUT
def hapus_transaksi():
    selected_item = tabel_ju.selection()
    if not selected_item:
        messagebox.showwarning("Peringatan", "Klik baris tabel yang ingin dihapus terlebih dahulu!")
        return
        
    values = tabel_ju.item(selected_item, "values")
    if values and values[0] == "TOTAL":
        messagebox.showwarning("Peringatan", "Baris TOTAL tidak bisa dihapus!")
        return
        
    index_terpilih = tabel_ju.index(selected_item)
    jawaban = messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin menghapus baris transaksi ini?")
    if jawaban:
        list_transaksi.pop(index_terpilih)
        tabel_ju.delete(selected_item)
        update_total_di_layar()
        messagebox.showinfo("Sukses", "Transaksi berhasil dihapus!")

# 6. PROSES VALIDASI BALANCE, BUKU BESAR 1 SHEET & NERACA LAJUR
def ekspor_siklus_akuntansi():
    if not list_transaksi:
        messagebox.showwarning("Peringatan", "Tidak ada data transaksi untuk diproses!")
        return
        
    df_ju = pd.DataFrame(list_transaksi)
    
    total_debit_ju = df_ju["Debit"].sum()
    total_kredit_ju = df_ju["Kredit"].sum()
    
    if total_debit_ju != total_kredit_ju:
        selisih = abs(total_debit_ju - total_kredit_ju)
        messagebox.showerror(
            "Gagal Proses (Tidak Balance)", 
            f"Jurnal Umum Anda tidak seimbang!\n\n"
            f"Total Debit: Rp {total_debit_ju:,.0f}\n"
            f"Total Kredit: Rp {total_kredit_ju:,.0f}\n"
            f"Selisih: Rp {selisih:,.0f}"
        )
        return

    baris_total_ju = pd.DataFrame([{"Tanggal": "TOTAL", "Keterangan": "", "Ref": "", "Debit": total_debit_ju, "Kredit": total_kredit_ju}])
    df_ju_excel = pd.concat([df_ju, baris_total_ju], ignore_index=True)
    
    list_bb_gabungan = []
    saldo_akhir_akun = {}
    
    for ref, info in master_akun.items():
        df_filter = df_ju[df_ju["Ref"] == ref].copy()
        
        list_bb_gabungan.append({
            "Tanggal": f"AKUN: {ref} - {info['Nama'].upper()}", 
            "Keterangan": "", "Ref": "", "Debit": "", "Kredit": "", "Saldo Kumulatif": ""
        })
        
        if not df_filter.empty:
            saldo_skrg = 0
            for _, row in df_filter.iterrows():
                if info["Normal"] == "Debit":
                    saldo_skrg += (row["Debit"] - row["Kredit"])
                else:
                    saldo_skrg += (row["Kredit"] - row["Debit"])
                
                list_bb_gabungan.append({
                    "Tanggal": row["Tanggal"], "Keterangan": row["Keterangan"].strip(), "Ref": row["Ref"],
                    "Debit": row["Debit"], "Kredit": row["Kredit"], "Saldo Kumulatif": saldo_skrg
                })
            saldo_akhir_akun[ref] = saldo_skrg
        else:
            list_bb_gabungan.append({
                "Tanggal": "- Belum ada mutasi transaksi -", "Keterangan": "", "Ref": "", "Debit": 0, "Kredit": 0, "Saldo Kumulatif": 0
            })
            saldo_akhir_akun[ref] = 0
            
        list_bb_gabungan.append({col: "" for col in ["Tanggal", "Keterangan", "Ref", "Debit", "Kredit", "Saldo Kumulatif"]})
        
    df_bb_tunggal = pd.DataFrame(list_bb_gabungan)

    data_nl = []
    for ref, info in master_akun.items():
        saldo = saldo_akhir_akun.get(ref, 0)
        ns_debit = saldo if info["Normal"] == "Debit" else 0
        ns_kredit = saldo if info["Normal"] == "Kredit" else 0
        
        lr_debit = ns_debit if ref.startswith(("4", "5")) else 0
        lr_kredit = ns_kredit if ref.startswith(("4", "5")) else 0
        
        n_debit = ns_debit if ref.startswith(("1", "2", "3")) else 0
        n_kredit = ns_kredit if ref.startswith(("1", "2", "3")) else 0
        
        data_nl.append({
            "Ref": ref, "Nama Akun": info["Nama"],
            "NS_Debit": ns_debit, "NS_Kredit": ns_kredit,
            "AJP_Debit": 0, "AJP_Kredit": 0,
            "NSSD_Debit": ns_debit, "NSSD_Kredit": ns_kredit,
            "LR_Debit": lr_debit, "LR_Kredit": lr_kredit,
            "N_Debit": n_debit, "N_Kredit": n_kredit
        })
        
    df_nl = pd.DataFrame(data_nl)
    
    total_row = {
        "Ref": "TOTAL", "Nama Akun": "",
        "NS_Debit": df_nl["NS_Debit"].sum(), "NS_Kredit": df_nl["NS_Kredit"].sum(),
        "AJP_Debit": 0, "AJP_Kredit": 0,
        "NSSD_Debit": df_nl["NSSD_Debit"].sum(), "NSSD_Kredit": df_nl["NSSD_Kredit"].sum(),
        "LR_Debit": df_nl["LR_Debit"].sum(), "LR_Kredit": df_nl["LR_Kredit"].sum(),
        "N_Debit": df_nl["N_Debit"].sum(), "N_Kredit": df_nl["N_Kredit"].sum()
    }
    df_nl = pd.concat([df_nl, pd.DataFrame([total_row])], ignore_index=True)

    try:
        if os.path.exists(nama_file):
            with pd.ExcelWriter(nama_file, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                df_ju_excel.to_excel(writer, sheet_name="Jurnal Umum", index=False)
                df_bb_tunggal.to_excel(writer, sheet_name="Buku Besar", index=False)
                df_nl.to_excel(writer, sheet_name="Neraca Lajur", index=False)
        else:
            with pd.ExcelWriter(nama_file, engine="openpyxl") as writer:
                df_ju_excel.to_excel(writer, sheet_name="Jurnal Umum", index=False)
                df_bb_tunggal.to_excel(writer, sheet_name="Buku Besar", index=False)
                df_nl.to_excel(writer, sheet_name="Neraca Lajur", index=False)
                        
        messagebox.showinfo("Sukses", f"Laporan disimpan ke:\n{nama_file}")
    except PermissionError:
        messagebox.showerror("Error", "Tutup dulu file Excel Anda sebelum menekan tombol proses.")

# 7. PEMBUATAN ANTARMUKA GUI APLIKASI
root = tk.Tk()
root.title("Sistem Akuntansi Otomatis")
root.geometry("700x650")

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

tk.Label(frame_input, text="Nominal (Rp):").grid(row=2, column=0, sticky="w")
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

btn_hapus = tk.Button(root, text="❌ Hapus Baris Terpilih yang Salah Input", 
                      command=hapus_transaksi, bg="#f44336", fg="white", font=("Arial", 9, "bold"))
btn_hapus.pack(padx=15, pady=5, anchor="e")

# Tombol Proses Siklus Akhir
btn_proses = tk.Button(root, text="⚡ PROSES JURNAL -> BUKU BESAR -> NERACA LAJUR", 
                       command=ekspor_siklus_akuntansi, bg="#2196F3", fg="white", font=("Arial", 11, "bold"))
btn_proses.pack(fill="x", padx=15, pady=15)

# PANGGIL FUNGSI UNTUK MEMBACA EXCEL LAMA SAAT GUI START
muat_data_dari_excel()

root.mainloop()
