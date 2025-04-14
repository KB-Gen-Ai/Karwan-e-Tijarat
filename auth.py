import streamlit as st
import sqlite3
from database import DB_PATH

def check_login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

def auth_section():
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("Login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT email FROM members WHERE email=? AND password=?", 
                             (email, password))
                result = cursor.fetchone()
                conn.close()
                if result:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error("Invalid credentials - Try registering first")

    with tab2:
        with st.form("Register"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Register"):
                if password != confirm_password:
                    st.error("Passwords don't match")
                else:
                    conn = sqlite3.connect(DB_PATH)
                    try:
                        # Insert with default empty values for other fields
                        conn.execute("""INSERT INTO members 
                                      (email, password, full_name, profession, expertise, can_help) 
                                      VALUES (?,?,?,?,?,?)""", 
                                    (email, password, "", "", "", ""))
                        conn.commit()
                        st.success("Registration successful! Please login")
                    except sqlite3.IntegrityError:
                        st.error("Email already registered - Try logging in instead")
                    finally:
                        conn.close()
