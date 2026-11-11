"""Tema tampilan bertema alpukat: hijau muda (daging), hijau tua (kulit), coklat (biji), dan putih.
Semua warna ada di satu tempat (bagian :root pada CSS) supaya mudah diganti."""
from urllib.parse import quote

import streamlit as st

KULIT, DAUN, DAGING, KRIM, BIJI, TINTA = "#1F3D28", "#3E6B3A", "#C9DF93", "#F4F8E2", "#6A4125", "#2B2119"


def alpukat_svg(lebar=64, kelas=""):
    """Gambar setengah buah alpukat: kulit hijau tua, daging hijau muda, biji coklat."""
    biji = ("<circle cx='50' cy='86' r='21' fill='%s'/><ellipse cx='43' cy='78' rx='6' ry='8' fill='#8B5A38' opacity='.75' "
            "transform='rotate(-25 43 78)'/>" % BIJI)
    return (f"<svg class='{kelas}' width='{lebar}' viewBox='0 0 100 130' xmlns='http://www.w3.org/2000/svg' aria-hidden='true'>"
            f"<path d='M50 3C71 3 75 30 85 52c14 28 7 73-35 73S1 80 15 52C25 30 29 3 50 3Z' fill='{KULIT}' stroke='#5C9150' stroke-width='3'/>"
            f"<path d='M50 15C65 15 68 37 76 56c11 24 5 58-26 58S13 80 24 56C32 37 35 15 50 15Z' fill='{DAGING}'/>"
            f"<path d='M50 36C60 36 63 50 68 62c8 18 4 44-18 44S24 80 32 62C37 50 40 36 50 36Z' fill='#E6F0B8'/>"
            f"{biji}</svg>")


def _dekor():
    """Avocado besar yang samar di pojok kanan bawah halaman."""
    svg = alpukat_svg(300).replace("class=''", "")
    return "url(\"data:image/svg+xml;utf8," + quote(svg) + "\")"


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=DM+Sans:wght@400;500;700&display=swap');
:root{--kulit:#1F3D28;--daun:#3E6B3A;--daging:#C9DF93;--krim:#F4F8E2;--biji:#6A4125;--biji2:#A06B43;--tinta:#2B2119;--garis:#DCE8B8;--putih:#fff}
html,body,.stApp,[data-testid="stAppViewContainer"]{font-family:'DM Sans',system-ui,sans-serif;color:var(--tinta)}
.stApp{background:var(--putih)}
.stApp::after{content:"";position:fixed;right:-70px;bottom:-60px;width:340px;height:440px;background:__DEKOR__ no-repeat center/contain;opacity:.07;pointer-events:none;z-index:0}
[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:2.2rem;max-width:1280px}

/* ---------- judul ---------- */
h1,h2,h3,h4{font-family:'Fraunces',Georgia,serif!important;color:var(--kulit)!important;letter-spacing:-.01em}
h1{font-size:2.15rem!important;font-weight:700!important;padding-bottom:.9rem!important;margin-bottom:.4rem;position:relative}
h1::after{content:"";position:absolute;left:0;bottom:0;width:78px;height:7px;border-radius:99px;background:linear-gradient(90deg,var(--biji) 0 38%,var(--daging) 38% 100%)}
h2,h3{font-weight:600!important}
.bagian{display:flex;align-items:center;gap:.6rem;font-family:'Fraunces',serif;font-weight:600;font-size:1.12rem;color:var(--kulit);margin:1.4rem 0 .7rem}
.bagian .biji{width:13px;height:13px;border-radius:50%;background:var(--biji);box-shadow:0 0 0 4px var(--daging)}
.bagian .no{width:27px;height:27px;border-radius:50%;background:var(--biji);color:#fff;font:700 .85rem 'DM Sans';display:grid;place-items:center;box-shadow:0 0 0 4px var(--daging)}

/* ---------- tombol (area utama dulu, sidebar sesudahnya agar menang saat spesifisitas sama) ---------- */
.stApp .stButton>button,.stApp .stFormSubmitButton>button{border-radius:12px;border:1.5px solid var(--daun);background:#fff;color:var(--kulit);font-weight:600;padding:.5rem 1.1rem;transition:all .15s}
.stApp .stButton>button:hover,.stApp .stFormSubmitButton>button:hover{background:var(--krim);border-color:var(--kulit);color:var(--kulit)}
.stApp .stButton>button[kind="primary"],.stApp .stFormSubmitButton>button[kind="primary"],.stApp button[data-testid="stBaseButton-primary"],.stApp button[data-testid="stBaseButton-primaryFormSubmit"]{background:var(--daun);color:#fff;border-color:var(--daun)}
.stApp .stButton>button[kind="primary"] *,.stApp button[data-testid="stBaseButton-primary"] *,.stApp button[data-testid="stBaseButton-primaryFormSubmit"] *{color:#fff!important}
.stApp .stButton>button[kind="primary"]:hover,.stApp button[data-testid="stBaseButton-primary"]:hover,.stApp button[data-testid="stBaseButton-primaryFormSubmit"]:hover{background:var(--biji);border-color:var(--biji)}
.stApp .stButton>button:disabled{opacity:.45}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:var(--kulit);border-right:0}
[data-testid="stSidebar"] *{color:#EEF4D6}
[data-testid="stSidebar"] .merek{display:flex;align-items:center;gap:.8rem;padding:.2rem .2rem 1rem;border-bottom:1px dashed rgba(201,223,147,.35);margin-bottom:.6rem}
[data-testid="stSidebar"] .merek b{font:700 1.25rem 'Fraunces',serif;color:#fff;display:block;line-height:1.1}
[data-testid="stSidebar"] .merek small{color:var(--daging);letter-spacing:.14em;font-size:.68rem;text-transform:uppercase}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,[data-testid="stSidebar"] .stCaption *{color:var(--daging)!important;letter-spacing:.16em;font-size:.68rem;font-weight:700}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],[data-testid="stSidebar"] .stCaption{margin-top:.9rem}
[data-testid="stSidebar"] .stButton>button{width:100%;justify-content:flex-start;text-align:left;border:0;background:transparent;color:#EEF4D6;box-shadow:none;border-radius:999px;padding:.38rem .95rem;font-weight:500;transition:background .15s,transform .15s}
[data-testid="stSidebar"] .stButton>button:hover{background:rgba(201,223,147,.16);border-color:transparent;color:#EEF4D6;transform:translateX(3px)}
[data-testid="stSidebar"] .stButton>button[kind="primary"],[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]{background:var(--daging);border-color:transparent;font-weight:700}
[data-testid="stSidebar"] .stButton>button[kind="primary"] *,[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] *{color:var(--kulit)!important}
[data-testid="stSidebar"] .stButton>button[kind="primary"]:hover,[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover{background:var(--daging);border-color:transparent}
[data-testid="stSidebar"] .stDownloadButton>button{background:var(--biji);border:0;border-radius:999px;width:100%;color:#fff}

/* ---------- isian ---------- */
[data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="textarea"]{border-radius:11px!important;border-color:var(--garis)!important;background:#fff!important}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within{border-color:var(--daun)!important;box-shadow:0 0 0 3px rgba(201,223,147,.55)!important}
label,[data-testid="stWidgetLabel"] p{font-weight:600;color:var(--kulit)!important;font-size:.88rem}
[data-testid="stExpander"]{border:1.5px solid var(--garis);border-radius:14px;background:#fff}
[data-testid="stTabs"] [role="tab"]{font-family:'Fraunces',serif;font-weight:600;font-size:1rem}
[data-testid="stTabs"] [aria-selected="true"]{color:var(--biji)!important}
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{background:var(--biji)!important;height:3px;border-radius:3px}

/* ---------- tabel ---------- */
.tbl{overflow:auto;max-height:68vh;background:#fff;border:1.5px solid var(--garis);border-radius:16px;margin:.2rem 0 1.2rem}
.tbl table{border-collapse:collapse;width:100%;font-size:14px}
.tbl th{position:sticky;top:0;background:var(--daging);color:var(--kulit);text-align:left;padding:10px 13px;white-space:nowrap;font-weight:700;letter-spacing:.02em;font-size:.8rem;text-transform:uppercase}
.tbl th.e{text-align:right}
.tbl td{padding:8px 13px;border-bottom:1px solid #EEF3DA;white-space:pre-wrap;color:var(--tinta)}
.tbl tbody tr:nth-child(even) td{background:#FBFDF3}
.tbl tbody tr:hover td{background:var(--krim)}
.tbl .e{text-align:right;font-variant-numeric:tabular-nums}
.tbl tr.b td{font-weight:700;background:var(--krim)!important;border-top:1.5px solid var(--biji2);color:var(--kulit)}
.tbl tr.kosong td{color:#8a8f7d;font-style:italic;text-align:center;padding:1.6rem}

/* ---------- beranda ---------- */
.hero{position:relative;overflow:hidden;background:var(--kulit);border-radius:26px 26px 26px 6px;padding:2rem 2.2rem;margin-bottom:1.3rem;display:flex;align-items:center;justify-content:space-between;gap:1rem}
.hero::before{content:"";position:absolute;right:-60px;top:-90px;width:300px;height:300px;border-radius:50%;background:var(--daun);opacity:.55}
.hero::after{content:"";position:absolute;left:38%;bottom:-70px;width:150px;height:150px;border-radius:50%;background:var(--biji);opacity:.5}
.hero .teks{position:relative;z-index:1}
.hero .kecil{color:var(--daging);letter-spacing:.2em;font-size:.72rem;font-weight:700;text-transform:uppercase}
.hero h2{color:#fff!important;font-size:2.3rem;margin:.3rem 0 .4rem;line-height:1.1}
.hero p{color:#DCE8B8;margin:0;max-width:30rem}
.hero svg{position:relative;z-index:1;flex:none;transform:rotate(8deg);filter:drop-shadow(0 12px 14px rgba(0,0,0,.25))}
.statistik{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:.9rem;margin-bottom:1.4rem}
.stat{background:#fff;border:1.5px solid var(--garis);border-radius:18px 18px 18px 5px;padding:.95rem 1.1rem;border-left:7px solid var(--daging)}
.stat:nth-child(2){border-left-color:var(--biji2)}
.stat:nth-child(3){border-left-color:var(--daun)}
.stat:nth-child(4){border-left-color:var(--biji2)}
.stat small{color:#6c7660;font-weight:700;letter-spacing:.06em;font-size:.7rem;text-transform:uppercase}
.stat b{display:block;font:700 1.45rem 'Fraunces',serif;color:var(--kulit);margin-top:.2rem}
.stat i{font-style:normal;color:#8a8f7d;font-size:.78rem}
.kartu{border-radius:22px 22px 6px 22px;padding:1.2rem 1.3rem;min-height:128px;margin-bottom:.5rem;position:relative;overflow:hidden}
.kartu h3{margin:0 0 .3rem!important;font-size:1.3rem}
.kartu p{margin:0;font-size:.9rem;opacity:.85}
.kartu::after{content:"";position:absolute;right:-26px;bottom:-26px;width:90px;height:90px;border-radius:50%;opacity:.35}
.kartu.k1{background:var(--daging)}.kartu.k1::after{background:var(--daun)}
.kartu.k2{background:#EBDAC6}.kartu.k2::after{background:var(--biji)}
.kartu.k3{background:var(--krim);border:1.5px dashed var(--daun)}.kartu.k3::after{background:var(--daging)}
.alur{display:flex;align-items:center;gap:.7rem;padding:.15rem 0}
.alur .titik{width:15px;height:15px;border-radius:50%;border:2.5px solid var(--daging);flex:none}
.alur .titik.ya{background:var(--daun);border-color:var(--daun)}
.catatan{background:var(--krim);border-left:6px solid var(--biji2);border-radius:6px 14px 14px 6px;padding:.7rem 1rem;margin:.6rem 0;color:var(--tinta);font-size:.92rem}
.total-box{display:inline-block;background:var(--krim);border:1.5px solid var(--daging);border-radius:14px 14px 14px 4px;padding:.55rem 1rem;margin:.4rem 0;font-weight:700;color:var(--kulit)}
.total-box span{font-family:'Fraunces',serif;font-size:1.25rem;color:var(--biji)}
.login-kartu{text-align:center;margin-top:1.5rem}
.login-kartu h1{font-size:2rem!important}
.login-kartu h1::after{left:50%;transform:translateX(-50%)}
</style>
"""


def terapkan():
    st.markdown(CSS.replace("__DEKOR__", _dekor()), unsafe_allow_html=True)
