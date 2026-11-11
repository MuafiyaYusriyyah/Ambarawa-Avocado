# Ambarawa Avocado - Siklus Akuntansi (Streamlit + MySQL)

## Menjalankan di komputer sendiri
1. Nyalakan MySQL (XAMPP: Start pada MySQL).
2. Di terminal VS Code: `pip install -r requirements.txt`
3. Koneksi database: default user `root`, tanpa password, database `alpukat estate`.
   Untuk mengubahnya, salin `.streamlit/secrets.toml.example` menjadi `.streamlit/secrets.toml` lalu isi.
   Hapus bagian `[admin]` di file itu bila tidak ingin memakai halaman login.
4. Jalankan: `streamlit run app.py` (browser terbuka di http://localhost:8501)

Tabel dan daftar akun dibuat otomatis saat pertama kali dibuka. Database dari versi lama otomatis dimigrasi
(nota lama pindah ke riwayat transaksi, akun Beban Air dan Beban Listrik ditambahkan).

## Struktur file: satu file untuk satu tahap siklus
```
app.py                      menyusun menu dan memanggil halaman (tidak berisi logika akuntansi)
core/                       fondasi: config.py (koneksi), db.py (tabel + akun awal), buku.py (muat data), util.py (format angka), konstanta.py
siklus/
  transaksi.py              INPUT: Penerimaan, Pengeluaran, Transaksi Lainnya -> otomatis jadi jurnal
  saldo_awal.py             0. Saldo awal
  ju.py                     1. Jurnal umum (+ form jurnal manual)
  persediaan.py             Kartu stok alpukat (rata-rata bergerak)
  bukbes.py                 2. Buku besar
  neraca_saldo.py           3. Neraca saldo
  ajp.py                    4. Jurnal penyesuaian
  bukbes_ajp.py             5. Buku besar setelah penyesuaian
  neraca_lajur.py           6. Neraca lajur
  laporan.py                7. Laporan keuangan (laba rugi, perubahan ekuitas, posisi keuangan)
  jurnal_penutup.py         8. Jurnal penutup
  neraca_saldo_akhir.py     9. Neraca saldo akhir
  daftar_akun.py            Daftar akun: tambah dan hapus
  ekspor.py                 Ekspor semua tabel ke Excel
ui/                         tema.py (warna + CSS), komponen.py (tabel, pesan), login.py, beranda.py
```
Tiap file siklus punya pola yang sama: fungsi `tabel(b)` untuk menyusun data dan fungsi `halaman()` untuk menampilkannya.

## Alur pemakaian
Semua transaksi dicatat lewat tiga menu **Input Transaksi**. Setiap transaksi otomatis mengalir ke seluruh siklus:

`Input` -> `Jurnal Umum` -> (`Kartu Stok` bila menyangkut alpukat) -> `Buku Besar` -> `Neraca Saldo` -> `Neraca Lajur` -> `Laporan Keuangan` -> `Jurnal Penutup` -> `Neraca Saldo Akhir`

| Menu | Isi daftar jenis transaksi |
|---|---|
| **Penerimaan** | Penjualan alpukat segar / frozen / untuk jus, penerimaan piutang, setoran modal, pendapatan lain-lain |
| **Pengeluaran** | Pembelian alpukat, bayar gaji, utang gaji, listrik, air, perawatan tanaman, ongkos kirim, produksi frozen, perlengkapan, kompensasi kerusakan, beban lainnya (pilih akun), bayar utang usaha, beli peralatan, prive |
| **Transaksi Lainnya** | Pembelian kredit, penjualan kredit, gaji terutang, beban terutang, pembelian peralatan kredit, produksi frozen |

Untuk transaksi alpukat, isi **jumlah (kg)** dan **harga per kg**; totalnya dihitung otomatis. Untuk transaksi lain cukup isi **nominal**.
Sebelum disimpan, halaman menampilkan pratinjau jurnal yang akan terbentuk. Penjualan otomatis mencatat HPP dan mengurangi stok.

Saldo awal, jurnal umum manual, dan jurnal penyesuaian tetap bisa diinput dari Beranda.

## Menghapus akun
Menu **Daftar Akun**, bagian *Hapus akun*. Akun hanya bisa dihapus bila belum dipakai jurnal, tidak punya saldo awal, dan bukan akun yang dikunci laporan
(Modal, Prive, Ikhtisar Laba Rugi, Pendapatan Lain-lain). Kolom *Status* menunjukkan alasan bila akun belum bisa dihapus.
Bila akun yang dihapus dibutuhkan sebuah jenis transaksi, jenis itu otomatis hilang dari daftar input dan Anda diberi tahu sebelum menghapus.

## Menaruh di hosting (Streamlit Community Cloud)
1. Siapkan MySQL yang bisa diakses dari internet (XAMPP di laptop tidak bisa). Contoh layanan: Aiven, TiDB Cloud, Railway.
2. Unggah folder ini ke repositori GitHub (secrets.toml tidak ikut karena sudah ada di .gitignore).
3. Di share.streamlit.io pilih repositori, file utama `app.py`.
4. Buka Settings > Secrets, isi seperti `secrets.toml.example`.
