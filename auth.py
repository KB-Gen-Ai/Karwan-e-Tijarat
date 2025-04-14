import streamlit as st

def check_login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

def login_form():
    with st.form("Login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            # Simple demo auth - replace with real validation
            if email and password:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.rerun()
