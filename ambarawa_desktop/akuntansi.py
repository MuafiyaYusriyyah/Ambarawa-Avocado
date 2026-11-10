"""Mesin siklus akuntansi.
Semua laporan DIHITUNG ULANG dari tiga sumber saja: saldo awal, jurnal umum (JU), jurnal penyesuaian (AJP).
Jadi cukup input di jurnal umum -> buku besar, neraca saldo, neraca lajur, laporan, penutup, dan
neraca saldo akhir otomatis ikut berubah.
"""
from collections import defaultdict
from decimal import Decimal as D

from db import cursor

Z = D("0")
LR = ("Pendapatan", "Pembelian", "HPP", "Beban")      # kelompok akun yang masuk kolom laba rugi
MODAL, PRIVE, IKHTISAR, LAIN = "3-101", "3-102", "3-103", "4-104"


def dec(v):
    return D(str(v)) if v not in (None, "") else Z


def sisi(net):
    """net (debit - kredit) -> (debit, kredit)."""
    return (net, Z) if net > 0 else (Z, abs(net))


def muat():
    with cursor() as c:
        c.execute("SELECT * FROM akun ORDER BY kode")
        akun = c.fetchall()
        c.execute("SELECT * FROM saldo_awal")
        sa = {r["kode"]: r for r in c.fetchall()}
        c.execute("SELECT * FROM pengaturan WHERE id=1")
        pg = c.fetchone()
        c.execute(
            """SELECT j.id, j.tanggal, j.bukti, j.keterangan, j.jenis, j.sumber, d.kode, d.debit, d.kredit
               FROM jurnal j JOIN jurnal_detail d ON d.jurnal_id=j.id
               WHERE j.jenis IN ('JU','AJP') ORDER BY j.tanggal, j.id, d.id"""
        )
        baris = c.fetchall()
    return Buku(akun, sa, baris, pg)


def daftar_jurnal(jenis):
    """Daftar jurnal (header + baris + total) untuk satu jenis: JU / AJP / PNT."""
    with cursor() as c:
        c.execute(
            """SELECT j.id, j.tanggal, j.bukti, j.keterangan, j.sumber, d.kode, a.nama, d.debit, d.kredit
               FROM jurnal j JOIN jurnal_detail d ON d.jurnal_id=j.id JOIN akun a ON a.kode=d.kode
               WHERE j.jenis=%s ORDER BY j.tanggal, j.id, d.id""",
            (jenis,),
        )
        rows = c.fetchall()
    hasil, idx = [], {}
    for r in rows:
        if r["id"] not in idx:
            idx[r["id"]] = dict(id=r["id"], tanggal=r["tanggal"], bukti=r["bukti"], ket=r["keterangan"],
                                sumber=r["sumber"], baris=[], d=Z, k=Z)
            hasil.append(idx[r["id"]])
        j = idx[r["id"]]
        j["baris"].append(dict(kode=r["kode"], nama=r["nama"], d=dec(r["debit"]), k=dec(r["kredit"])))
        j["d"] += dec(r["debit"])
        j["k"] += dec(r["kredit"])
    return hasil, sum((j["d"] for j in hasil), Z), sum((j["k"] for j in hasil), Z)


class Buku:
    def __init__(self, akun, sa, baris, pengaturan):
        self.akun = akun
        self.a = {x["kode"]: x for x in akun}
        self.sa = sa
        self.baris = baris
        self.pg = pengaturan

    # ---------- dasar ----------
    def awal(self, kode):
        r = self.sa.get(kode)
        return (dec(r["debit"]), dec(r["kredit"])) if r else (Z, Z)

    def mut(self, jenis):
        m = defaultdict(lambda: [Z, Z])
        for l in self.baris:
            if l["jenis"] in jenis:
                m[l["kode"]][0] += dec(l["debit"])
                m[l["kode"]][1] += dec(l["kredit"])
        return m

    def net(self, jenis):
        """Saldo bersih (debit - kredit) tiap akun = saldo awal + mutasi jenis jurnal tertentu."""
        m = self.mut(jenis)
        out = {}
        for a in self.akun:
            d0, k0 = self.awal(a["kode"])
            d, k = m[a["kode"]] if a["kode"] in m else (Z, Z)
            out[a["kode"]] = d0 - k0 + d - k
        return out

    def natural(self, net, kode):
        """Saldo menurut sisi normal akun (positif = bertambah di sisi normal)."""
        return net if self.a[kode]["saldo_normal"] == "D" else -net

    def awal_sudah_diisi(self):
        return any(dec(r["debit"]) or dec(r["kredit"]) for r in self.sa.values())

    # ---------- 2. buku besar (satu sheet untuk semua akun) ----------
    def buku_besar(self, jenis=("JU",)):
        per_akun = defaultdict(list)
        for l in self.baris:
            if l["jenis"] in jenis:
                per_akun[l["kode"]].append(l)
        hasil = []
        for a in self.akun:
            kode = a["kode"]
            tanda = 1 if a["saldo_normal"] == "D" else -1
            rows, saldo = [], Z
            d0, k0 = self.awal(kode)
            if d0 or k0:
                saldo += (d0 - k0) * tanda
                rows.append(dict(tgl=None, ket="Saldo awal", bukti="SA", jenis="SA", d=d0, k=k0, saldo=saldo))
            for l in per_akun.get(kode, []):
                d, k = dec(l["debit"]), dec(l["kredit"])
                saldo += (d - k) * tanda
                rows.append(dict(tgl=l["tanggal"], ket=l["keterangan"], bukti=l["bukti"], jenis=l["jenis"],
                                 d=d, k=k, saldo=saldo))
            if rows:
                hasil.append(dict(kode=kode, nama=a["nama"], normal=a["saldo_normal"], baris=rows,
                                  td=sum((r["d"] for r in rows), Z), tk=sum((r["k"] for r in rows), Z), saldo=saldo))
        return hasil

    # ---------- 3. neraca saldo ----------
    def neraca_saldo(self):
        net = self.net(("JU",))
        rows = []
        for a in self.akun:
            n = net[a["kode"]]
            if n != 0:
                d, k = sisi(n)
                rows.append(dict(kode=a["kode"], nama=a["nama"], d=d, k=k))
        return rows, sum((r["d"] for r in rows), Z), sum((r["k"] for r in rows), Z)

    # ---------- 6. neraca lajur ----------
    def neraca_lajur(self):
        ns, aj = self.net(("JU",)), self.mut(("AJP",))
        kolom = ["ns_d", "ns_k", "aj_d", "aj_k", "na_d", "na_k", "lr_d", "lr_k", "nr_d", "nr_k"]
        tot = {k: Z for k in kolom}
        rows = []
        for a in self.akun:
            kode = a["kode"]
            n = ns[kode]
            ajd, ajk = aj[kode] if kode in aj else (Z, Z)
            na = n + ajd - ajk
            if n == 0 and ajd == 0 and ajk == 0 and na == 0:
                continue
            r = dict(kode=kode, nama=a["nama"], aj_d=ajd, aj_k=ajk)
            r["ns_d"], r["ns_k"] = sisi(n)
            r["na_d"], r["na_k"] = sisi(na)
            if a["kelompok"] in LR:
                r["lr_d"], r["lr_k"], r["nr_d"], r["nr_k"] = r["na_d"], r["na_k"], Z, Z
            else:
                r["lr_d"], r["lr_k"], r["nr_d"], r["nr_k"] = Z, Z, r["na_d"], r["na_k"]
            for k in kolom:
                tot[k] += r[k]
            rows.append(r)
        laba = tot["lr_k"] - tot["lr_d"]               # > 0 laba, < 0 rugi
        sel = {k: Z for k in kolom}
        if laba >= 0:                                   # laba: LR debit & neraca kredit
            sel["lr_d"], sel["nr_k"] = laba, laba
        else:                                           # rugi: LR kredit & neraca debit
            sel["lr_k"], sel["nr_d"] = -laba, -laba
        akhir = {k: tot[k] + sel[k] for k in kolom}
        return dict(rows=rows, tot=tot, sel=sel, akhir=akhir, laba=laba,
                    status="Laba" if laba >= 0 else "Rugi", besar=abs(laba))

    # ---------- 7. laporan keuangan ----------
    def laporan(self):
        net = self.net(("JU", "AJP"))
        amt = lambda k: self.natural(net[k], k)

        def baris(filter_fn):
            return [dict(kode=a["kode"], nama=a["nama"], jml=amt(a["kode"]), normal=a["saldo_normal"])
                    for a in self.akun if filter_fn(a) and amt(a["kode"]) != 0]

        pend = baris(lambda a: a["kelompok"] == "Pendapatan" and a["kode"] != LAIN and a["saldo_normal"] == "K")
        poto = baris(lambda a: a["kelompok"] == "Pendapatan" and a["saldo_normal"] == "D")
        lain = baris(lambda a: a["kode"] == LAIN)
        beli = baris(lambda a: a["kelompok"] == "Pembelian")
        hpp = baris(lambda a: a["kelompok"] == "HPP")
        beban = baris(lambda a: a["kelompok"] == "Beban")
        s = lambda xs: sum((x["jml"] for x in xs), Z)

        penjualan_bersih = s(pend) - s(poto)
        pembelian_bersih = sum((x["jml"] if x["normal"] == "D" else -x["jml"] for x in beli), Z)
        total_hpp = pembelian_bersih + s(hpp)
        laba_kotor = penjualan_bersih - total_hpp
        laba_usaha = laba_kotor - s(beban)
        laba = laba_usaha + s(lain)
        lr = dict(pend=pend, poto=poto, penjualan_bersih=penjualan_bersih, beli=beli,
                  pembelian_bersih=pembelian_bersih, hpp=hpp, total_hpp=total_hpp, laba_kotor=laba_kotor,
                  beban=beban, total_beban=s(beban), laba_usaha=laba_usaha, lain=lain, laba=laba)

        # perubahan ekuitas
        d0, k0 = self.awal(MODAL)
        modal_awal = k0 - d0
        modal_mut = self.mut(("JU", "AJP"))
        md, mk = modal_mut[MODAL] if MODAL in modal_mut else (Z, Z)
        tambahan = mk - md
        prive = amt(PRIVE)
        modal_akhir = modal_awal + tambahan + laba - prive
        ek = dict(modal_awal=modal_awal, tambahan=tambahan, laba=laba, prive=prive, modal_akhir=modal_akhir)

        # posisi keuangan
        lancar = baris(lambda a: a["kelompok"] == "Aset" and a["kode"] < "1-106")
        tetap = baris(lambda a: a["kelompok"] == "Aset" and a["kode"] >= "1-106")
        for x in lancar + tetap:      # akumulasi penyusutan tampil sebagai pengurang (negatif)
            x["jml"] = net[x["kode"]]
        liab = baris(lambda a: a["kelompok"] == "Liabilitas")
        total_aset = s(lancar) + s(tetap)
        total_liab = s(liab)
        pos = dict(lancar=lancar, tetap=tetap, total_lancar=s(lancar), total_tetap=s(tetap), total_aset=total_aset,
                   liab=liab, total_liab=total_liab, modal_akhir=modal_akhir,
                   total_pasiva=total_liab + modal_akhir, seimbang=(total_aset == total_liab + modal_akhir))
        return dict(lr=lr, ek=ek, pos=pos)

    # ---------- 8. jurnal penutup ----------
    def penutup(self):
        net = self.net(("JU", "AJP"))
        tgl = self.pg["tgl_akhir"] if self.pg else None
        nama = lambda k: self.a[k]["nama"]
        sementara = [a for a in self.akun if a["kelompok"] in LR and net[a["kode"]] != 0]
        kredit_saldo = [a for a in sementara if net[a["kode"]] < 0]
        debit_saldo = [a for a in sementara if net[a["kode"]] > 0]
        ent = []

        def tambah(ket, baris):
            td = sum((b[2] for b in baris), Z)
            tk = sum((b[3] for b in baris), Z)
            ent.append(dict(no=len(ent) + 1, tanggal=tgl, ket=ket, td=td, tk=tk,
                            baris=[dict(kode=b[0], nama=b[1], d=b[2], k=b[3]) for b in baris]))

        if kredit_saldo:
            tot = sum((-net[a["kode"]] for a in kredit_saldo), Z)
            tambah("Menutup akun pendapatan / akun bersaldo kredit ke Ikhtisar Laba Rugi",
                   [(a["kode"], a["nama"], -net[a["kode"]], Z) for a in kredit_saldo]
                   + [(IKHTISAR, nama(IKHTISAR), Z, tot)])
        if debit_saldo:
            tot = sum((net[a["kode"]] for a in debit_saldo), Z)
            tambah("Menutup akun HPP, beban & akun bersaldo debit ke Ikhtisar Laba Rugi",
                   [(IKHTISAR, nama(IKHTISAR), tot, Z)]
                   + [(a["kode"], a["nama"], Z, net[a["kode"]]) for a in debit_saldo])
        laba = -sum((net[a["kode"]] for a in sementara), Z)
        if laba > 0:
            tambah("Menutup Ikhtisar Laba Rugi (laba) ke Modal Pemilik",
                   [(IKHTISAR, nama(IKHTISAR), laba, Z), (MODAL, nama(MODAL), Z, laba)])
        elif laba < 0:
            tambah("Menutup Ikhtisar Laba Rugi (rugi) ke Modal Pemilik",
                   [(MODAL, nama(MODAL), -laba, Z), (IKHTISAR, nama(IKHTISAR), Z, -laba)])
        if net[PRIVE] > 0:
            tambah("Menutup Prive ke Modal Pemilik",
                   [(MODAL, nama(MODAL), net[PRIVE], Z), (PRIVE, nama(PRIVE), Z, net[PRIVE])])
        return ent, sum((e["td"] for e in ent), Z), sum((e["tk"] for e in ent), Z)

    # ---------- 9. neraca saldo akhir (setelah penutup) ----------
    def saldo_akhir(self):
        net = self.net(("JU", "AJP"))
        modal_akhir = self.laporan()["ek"]["modal_akhir"]
        rows = []
        for a in self.akun:
            if a["kelompok"] not in ("Aset", "Liabilitas", "Ekuitas"):
                continue
            kode = a["kode"]
            if kode in (PRIVE, IKHTISAR):
                n = Z
            elif kode == MODAL:
                n = -modal_akhir
            else:
                n = net[kode]
            if n != 0:
                d, k = sisi(n)
                rows.append(dict(kode=kode, nama=a["nama"], d=d, k=k))
        return rows, sum((r["d"] for r in rows), Z), sum((r["k"] for r in rows), Z)
