import streamlit as st
import pandas as pd
import bcrypt
import os

# -----------------------------
# Load user data from Excel
# -----------------------------
# dossier où se trouve loginpage.py (=> src/pages)
BASE_DIR = os.path.dirname(__file__)

# on remonte d'un cran pour arriver dans src/
USER_FILE = os.path.join(BASE_DIR, "..", "users.xlsx")

@st.cache_data
def load_users():
    # construire le chemin absolu
    excel_path = os.path.abspath(USER_FILE)

    return pd.read_excel(excel_path)

users_df = load_users()

# Masquer le menu de navigation par défaut de Streamlit
hide_pages_style = """
    <style>
    div[data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_pages_style, unsafe_allow_html=True)

# -----------------------------
# Page Styling
# -----------------------------
page_bg = """
<style>
.stApp {
    background-color: #2c2f5b; /* dark background */
}
.stTextInput>div>div>input {
    border-radius: 8px;
    padding: 10px;
}
.stButton>button {
    width: 100%;
    background-color: #00cfff;
    color: white;
    font-weight: bold;
    border-radius: 8px;
    padding: 10px;
}
.stButton>button:hover {
    background-color: #00a0cc;
}
/* Forgot password link-style */
div[data-testid="stVerticalBlock"] button[kind="secondary"] {
    background: none !important;
    color: gray !important;
    font-size: 12px !important;
    text-decoration: underline;
    width: auto !important;
    border: none !important;
    padding: 0 !important;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# -----------------------------
# Layout: 2 columns
# -----------------------------
col1, col2 = st.columns([1,1])  # left = logo, right = login form

with col1:
    BASE_DIR = os.path.dirname(__file__)  # src/pages
    IMG_PATH = os.path.join(BASE_DIR, "..", "bankofalgerialogo.png")

    st.image(IMG_PATH, width=350)



with col2:
    st.markdown("<h2 style='color:white;'>Welcome Back!</h2>", unsafe_allow_html=True)

    # inputs
    username = st.text_input("username")
    password = st.text_input("Password", type="password", help="Enter your password")

    # Sign In button (kept as normal button)
    if st.button("Sign In"):
        if (not username) or (not password):
            st.warning("⚠️ Please enter both username and password.")
        else:
            if username in users_df['username'].values:
                stored_password = users_df.loc[users_df['username'] == username, 'password'].values[0]
                # Plain text password check
                if str(password) == str(stored_password):
                    st.success(f"✅ Welcome {username}!")
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()  # Redémarrer pour afficher la redirection
                else:
                    st.error("❌ Invalid username or password.")
            else:
                st.error("❌ Invalid username or password.")

    # Forgot password (small button styled as link)
    if st.button("Forgot my password", key="forgot_pwd"):
        st.info("🔒 Please contact administrator to reset your password")

# -----------------------------
# Redirection après connexion réussie
# -----------------------------
if st.session_state.get('authenticated', False):
  st.switch_page("front.py")