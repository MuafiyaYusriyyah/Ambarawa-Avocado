"""Memuat data buku sekali (akun, saldo awal, jurnal), lalu dipakai bersama oleh semua tahap siklus."""
from collections import defaultdict

from core.db import ambil
from core.util import Z, dec


class Buku:
    """Sumber data hanya tiga: saldo awal, jurnal umum (JU), dan jurnal penyesuaian (AJP).
    Transaksi penerimaan / pengeluaran / lainnya otomatis menjadi JU, jadi semuanya ikut terhitung di sini."""

    def __init__(self):
        self.akun = ambil("SELECT * FROM akun ORDER BY kode")
        self.a = {x["kode"]: x for x in self.akun}
        self.sa = {x["kode"]: (dec(x["debit"]), dec(x["kredit"]), dec(x["qty"])) for x in ambil("SELECT * FROM saldo_awal")}
        self.pg = ambil("SELECT * FROM pengaturan WHERE id=1")[0]
        self.baris = [dict(x, debit=dec(x["debit"]), kredit=dec(x["kredit"])) for x in ambil(
            "SELECT j.tanggal,j.bukti,j.keterangan,j.jenis,d.kode,d.debit,d.kredit FROM jurnal j "
            "JOIN jurnal_detail d ON d.jurnal_id=j.id WHERE j.jenis IN ('JU','AJP') ORDER BY j.tanggal,j.id,d.id")]
        self._lap = None

    def mut(self, jenis):
        """Total mutasi debit dan kredit tiap akun untuk jenis jurnal tertentu."""
        m = defaultdict(lambda: [Z, Z])
        for l in self.baris:
            if l["jenis"] in jenis:
                m[l["kode"]][0] += l["debit"]
                m[l["kode"]][1] += l["kredit"]
        return m

    def net(self, jenis):
        """Saldo bersih (debit - kredit) tiap akun = saldo awal + mutasi jurnal."""
        m = self.mut(jenis)
        return {k: self.sa.get(k, (Z, Z, Z))[0] - self.sa.get(k, (Z, Z, Z))[1] + m[k][0] - m[k][1] for k in self.a}
