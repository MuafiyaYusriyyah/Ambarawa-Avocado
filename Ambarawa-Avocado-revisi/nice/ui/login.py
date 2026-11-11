"""Gerbang masuk. Pilihan (di .streamlit/secrets.toml atau Settings > Secrets pada Streamlit Cloud):
  [admin] username + password   -> halaman login dengan username dan password
  app_password                  -> cukup satu kata sandi
  keduanya kosong               -> aplikasi terbuka tanpa login (cocok untuk dipakai di komputer sendiri)"""
import streamlit as st

from ui.tema import alpukat_svg


def _rahasia(*kunci):
    try:
        x = st.secrets
        for k in kunci:
            x = x[k]
        return x
    except Exception:
        return None


def perlu_login():
    return bool((_rahasia("admin", "username") and _rahasia("admin", "password")) or _rahasia("app_password"))


def gerbang():
    """Hentikan halaman dengan form login bila belum masuk."""
    if not perlu_login() or st.session_state.get("masuk"):
        return
    user, pw, sandi = _rahasia("admin", "username"), _rahasia("admin", "password"), _rahasia("app_password")
    _, tengah, _ = st.columns([1, 1.6, 1])
    with tengah:
        st.markdown(f"<div class='login-kartu'>{alpukat_svg(86)}<h1>Ambarawa Avocado</h1>"
                    "<p>Sistem akuntansi kebun alpukat. Silakan masuk untuk melanjutkan.</p></div>", unsafe_allow_html=True)
        with st.form("form_login"):
            u = st.text_input("Username") if user and pw else None
            p = st.text_input("Password" if user and pw else "Kata sandi", type="password")
            kirim = st.form_submit_button("Masuk", use_container_width=True, type="primary")
        if kirim:
            benar = (u == str(user) and p == str(pw)) if user and pw else p == str(sandi)
            if benar:
                st.session_state["masuk"] = True
                st.rerun()
            st.error("Username atau password salah." if user and pw else "Kata sandi salah.")
    st.stop()


def tombol_keluar():
    """Tombol keluar di sidebar, hanya muncul bila login dipakai."""
    if perlu_login() and st.sidebar.button("Keluar", key="m_keluar_login"):
        st.session_state["masuk"] = False
        st.rerun()
