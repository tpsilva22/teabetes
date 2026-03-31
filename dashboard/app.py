import streamlit as st

st.set_page_config(
    page_title="TeaBetes",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

USERS = {
    "admin": {"password": "admin", "name": "Dr. Divaldo Dias"},
}

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Lora:wght@500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
[data-testid="collapsedControl"] { display: none; }
.block-container { padding-top: 2rem !important; }

/* Landing */
.land-logo  { font-family:'Lora',serif; font-size:2.2rem; color:#4da6d9;
              text-align:center; margin-bottom:6px; }
.land-sub   { text-align:center; opacity:.45; font-size:.88rem; margin-bottom:36px; }
.card-grid  { display:grid; grid-template-columns:1fr 1fr; gap:18px;
              max-width:620px; width:100%; margin:0 auto; }
.sel-card   { border:1px solid rgba(128,128,128,.2); border-radius:16px;
              padding:32px 26px; text-align:center;
              box-shadow:0 4px 20px rgba(0,0,0,.1); }
.sel-card-title { font-family:'Lora',serif; font-size:1.2rem;
                  color:#4da6d9; margin-bottom:6px; }
.sel-card-desc  { font-size:.82rem; opacity:.5; line-height:1.6; }

/* Login */
.login-title { font-family:'Lora',serif; font-size:1.6rem;
               color:#4da6d9; text-align:center; margin-bottom:4px; }
.login-sub   { text-align:center; opacity:.45; font-size:.82rem; margin-bottom:26px; }
.login-box   { border:1px solid rgba(128,128,128,.2); border-radius:16px;
               padding:36px 32px; box-shadow:0 6px 32px rgba(0,0,0,.14); }
.err-box     { background:rgba(220,38,38,.1); border:1px solid rgba(220,38,38,.3);
               color:#f87171; padding:10px 14px; border-radius:8px;
               font-size:.84rem; margin-bottom:10px; }

/* Shared buttons */
div[data-testid="stButton"] > button {
    background:#1a5f8a !important; color:#fff !important; border:none !important;
    border-radius:8px !important; padding:.52rem 1rem !important;
    font-weight:500 !important; width:100% !important; margin-top:5px;
    font-family:'Inter',sans-serif !important;
}
div[data-testid="stButton"] > button:hover { background:#236d9e !important; }
div[data-testid="stTextInput"] input { border-radius:7px !important; }
</style>
""", unsafe_allow_html=True)


# ── Auth ──────────────────────────────────────────────────────────────────────
def do_login(username, password):
    user = USERS.get(username)
    if user and user["password"] == password:
        st.session_state.update(logged_in=True, name=user["name"])
        return True
    return False

def logout():
    st.session_state.clear()
    st.rerun()


# ── Landing ───────────────────────────────────────────────────────────────────
def show_landing():
    st.markdown("<div style='height:3rem'></div>", unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("""
        <div style="text-align:center; margin-bottom:2.5rem">
            <div class="land-logo">🩺 TeaBetes</div>
            <div class="land-sub">Diabetes Analysis Dashboard</div>
        </div>
        """, unsafe_allow_html=True)

    _, card1, gap, card2, _ = st.columns([1, 3, 0.3, 3, 1])
    with card1:
        st.markdown("""
        <div class="sel-card">
            <div class="sel-card-title">Health Explorer</div>
            <div class="sel-card-desc">Input your data and explore your risk profile with real-time interactive charts.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Explore without an account", key="go_patient", use_container_width=True):
            st.session_state.view = "patient"; st.rerun()

    with card2:
        st.markdown("""
        <div class="sel-card">
            <div class="sel-card-title">Clinical Area</div>
            <div class="sel-card-desc">Population analysis, metabolic correlations, and risk group identification. Login required.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Login as Doctor", key="go_login", use_container_width=True):
            st.session_state.view = "login"; st.rerun()


# ── Login ─────────────────────────────────────────────────────────────────────
def show_login():
    st.markdown("<style>[data-testid='stSidebar']{display:none}</style>", unsafe_allow_html=True)

    col_info, col_form = st.columns([1, 1], gap="large")

    with col_info:
        st.markdown("""
        <div style="padding:3rem 2rem 0 2rem">
            <div style="font-family:'Lora',serif;font-size:1.8rem;color:#4da6d9;margin-bottom:14px">
                Clinical Area
            </div>
            <div style="opacity:.55;font-size:.9rem;line-height:1.75;margin-bottom:20px">
                Exclusive access for healthcare professionals.<br><br>
                Visualise stage distribution, analyse metabolic correlations,
                compare risk groups by age, and explore the complete dataset
                with interactive charts.
            </div>
            <div style="opacity:.3;font-size:.76rem;border-top:1px solid rgba(128,128,128,.2);padding-top:14px">
                Demo &mdash; user: <code>admin</code> &nbsp;/&nbsp; password: <code>admin</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_form:
        st.markdown("<div style='height:2.5rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">🩺 TeaBetes</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Healthcare Professionals</div>', unsafe_allow_html=True)

        username = st.text_input("User", placeholder="admin", key="login_user")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="login_pw")

        if st.session_state.get("login_error"):
            st.markdown('<div class="err-box">Incorrect credentials.</div>', unsafe_allow_html=True)

        if st.button("Login", key="do_login"):
            if do_login(username, password):
                st.session_state.login_error = False
                st.session_state.view = "doctor"
                st.rerun()
            else:
                st.session_state.login_error = True
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("Back to Home", key="back_login"):
            st.session_state.view = "landing"
            st.session_state.login_error = False
            st.rerun()


# ── Router ────────────────────────────────────────────────────────────────────
view = st.session_state.get("view", "landing")

if view == "landing":
    st.markdown("<style>[data-testid='stSidebar']{display:none}</style>", unsafe_allow_html=True)
    show_landing()

elif view == "login":
    show_login()

elif view == "doctor":
    if not st.session_state.get("logged_in"):
        st.session_state.view = "login"; st.rerun()
    import pages.doctor as page
    page.show(logout_fn=logout)

elif view == "patient":
    def go_back():
        st.session_state.view = "landing"; st.rerun()
    import pages.patient as page
    page.show(back_fn=go_back)