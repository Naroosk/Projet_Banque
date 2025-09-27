import streamlit as st
import pandas as pd
import bcrypt

# -----------------------------
# Load user data from Excel
# -----------------------------
USER_FILE = r"C:\Users\HP\Downloads\BI_BA\Stage\src\users.xlsx"

@st.cache_data
def load_users():
    df = pd.read_excel(USER_FILE)
    return df

users_df = load_users()

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
    st.image(r"C:\Users\HP\Downloads\BI_BA\Stage\src\bankofalgerialogo.png", width=350)  # logo on the left

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