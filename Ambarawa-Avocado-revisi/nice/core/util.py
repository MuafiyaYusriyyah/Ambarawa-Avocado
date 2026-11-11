"""Alat bantu umum: format angka, baca input angka dan tanggal, serta pembentuk baris tabel."""
import datetime as dt
from decimal import Decimal as D, InvalidOperation

Z = D(0)
BULAN = "Jan Feb Mar Apr Mei Jun Jul Agu Sep Okt Nov Des".split()
I = "      "          # indentasi untuk akun yang berada di sisi kredit / rincian


# ------------------------------------------------------------------ angka dan tanggal
def dec(v):
    return D(str(v)) if v not in (None, "") else Z


def rp(v, nol="-"):
    """1500000 -> '1.500.000'; negatif dalam kurung; nol diganti teks `nol`."""
    v = dec(v)
    if v == 0:
        return nol
    s = f"{abs(v):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    s = s[:-3] if s.endswith(",00") else s
    return f"({s})" if v < 0 else s


def tgl(v):
    return f"{v.day:02d} {BULAN[v.month - 1]} {v.year}" if v else ""


def angka(s, uang=True):
    """'1.500.000', '1500000', '1500,50' -> Decimal. Angka (int, float, Decimal) langsung dikonversi."""
    if isinstance(s, (int, float, D)):
        return D(str(round(s, 2)))
    s = (s or "").strip().lower().replace("rp", "").replace(" ", "")
    if not s:
        return Z
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif uang and (s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[1]) == 3)):
        s = s.replace(".", "")
    try:
        return D(s)
    except InvalidOperation:
        raise ValueError(f"Angka tidak valid: {s}")


def tanggal(s):
    """Teks HH-BB-TTTT (atau objek tanggal) -> date."""
    if isinstance(s, dt.date):
        return s
    for f in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime((s or "").strip(), f).date()
        except ValueError:
            pass
    raise ValueError("Tanggal tidak valid. Tulis HH-BB-TTTT, contoh 31-12-2026.")


# ------------------------------------------------------------------ bentuk tabel
# kolom: (judul, lebar, rata)   baris: (isi sel, tag, iid)   tag "b" = tebal, "kosong" = pesan kosong
def kol(*spek):
    return [(j, w, r) for j, w, r in spek]


def B(*sel, tag=None):
    return list(sel), tag


def sisi(n):
    """saldo bersih (debit - kredit) -> (debit, kredit)"""
    return (n, Z) if n > 0 else (Z, abs(n))
