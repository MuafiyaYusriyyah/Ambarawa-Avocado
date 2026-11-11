"""Akun-akun yang dipakai langsung oleh perhitungan laporan. Akun ini tidak boleh dihapus."""

# kelompok akun yang masuk kolom laba rugi
LR = ("Pendapatan", "Pembelian", "HPP", "Beban")

MODAL = "3-101"      # Modal Pemilik
PRIVE = "3-102"      # Prive
IKHTISAR = "3-103"   # Ikhtisar Laba Rugi
LAIN = "4-104"       # Pendapatan Lain-lain

DIKUNCI = (MODAL, PRIVE, IKHTISAR, LAIN)

# akun persediaan yang punya kartu stok (kg)
STOK = {"1-104": "Alpukat Segar", "1-105": "Alpukat Frozen"}
