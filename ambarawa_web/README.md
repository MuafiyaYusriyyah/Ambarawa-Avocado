# Ambarawa Avocado - Siklus Akuntansi (Streamlit + MySQL)

## Menjalankan di komputer sendiri
1. Nyalakan MySQL (XAMPP: Start pada MySQL).
2. Di terminal VS Code: `pip install -r requirements.txt`
3. Koneksi database: default user `root`, tanpa password, database `alpukat estate`.
   Untuk mengubahnya, salin `.streamlit/secrets.toml.example` menjadi `.streamlit/secrets.toml` lalu isi.
4. Jalankan: `streamlit run app.py` (browser terbuka di http://localhost:8501)

Tabel dan daftar akun dibuat otomatis saat pertama kali dibuka.

## Menaruh di hosting (Streamlit Community Cloud)
1. Siapkan MySQL yang bisa diakses dari internet (XAMPP di laptop tidak bisa). Contoh layanan: Aiven, TiDB Cloud, Railway.
2. Unggah folder ini ke repositori GitHub (secrets.toml tidak ikut karena sudah ada di .gitignore).
3. Di share.streamlit.io pilih repositori, file utama `app.py`.
4. Buka Settings > Secrets, isi seperti `secrets.toml.example`: bagian `[mysql]` dari penyedia database, dan `app_password` agar halaman tidak terbuka untuk umum.

## Alur pemakaian
Semua input lewat tombol di Beranda: Saldo Awal, Jurnal Umum, Jurnal Penyesuaian, Penjualan, Pembelian, Produksi Frozen.
Nota penjualan dan pembelian otomatis membuat jurnal umum, kartu stok, dan buku besar.
