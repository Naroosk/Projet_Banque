import streamlit as st
import pandas as pd
import bcrypt
import os

# -----------------------------
# Load user data from Excel
# -----------------------------
BASE_DIR = os.path.dirname(__file__)  # src/pages
USER_FILE = os.path.join(BASE_DIR, "..", "users.xlsx")

@st.cache_data
def load_users():
    excel_path = os.path.abspath(USER_FILE)
    return pd.read_excel(excel_path)

users_df = load_users()

# -----------------------------
# Masquer complètement la sidebar
# -----------------------------
hide_sidebar_style = """
    <style>
    /* Masquer le conteneur complet de la sidebar */
    section[data-testid="stSidebar"] {display: none !important;}
    /* Ajuster la largeur du contenu principal */
    div[data-testid="stAppViewContainer"] {
        margin-left: 0 !important;
        padding-left: 0 !important;
    }
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

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
# Layout: 2 columns (logo + login form)
# -----------------------------
col1, col2 = st.columns([1, 1])

with col1:
    IMG_PATH = os.path.join(BASE_DIR, "..", "bankofalgerialogo.png")
    st.image(IMG_PATH, width=350)

with col2:
    st.markdown("<h2 style='color:white;'>Welcome Back!</h2>", unsafe_allow_html=True)

    username = st.text_input("username")
    password = st.text_input("Password", type="password", help="Enter your password")

    if st.button("Sign In"):
        if (not username) or (not password):
            st.warning("⚠️ Please enter both username and password.")
        else:
            if username in users_df['username'].values:
                stored_password = users_df.loc[users_df['username'] == username, 'password'].values[0]
                if str(password) == str(stored_password):
                    st.success(f"✅ Welcome {username}!")
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()  # redémarre pour afficher la redirection
                else:
                    st.error("❌ Invalid username or password.")
            else:
                st.error("❌ Invalid username or password.")

    if st.button("Forgot my password", key="forgot_pwd"):
        st.info("🔒 Please contact administrator to reset your password")

# -----------------------------
# Redirection après connexion réussie
# -----------------------------
if st.session_state.get('authenticated', False):
    st.switch_page("front.py")
