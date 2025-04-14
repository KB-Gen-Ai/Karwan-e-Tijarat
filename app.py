import streamlit as st
import sqlite3
from uuid import uuid4
from datetime import datetime
from database import init_db

# Initialize database
init_db()

# --- Streamlit UI ---
st.set_page_config(page_title="Karwan-e-Tijarat", page_icon="🤝")

def register_member():
    st.header("🌟 Join Karwan-e-Tijarat")
    with st.form("registration_form"):
        name = st.text_input("Full Name*")
        profession = st.text_input("Profession*")
        expertise = st.text_input("Expertise (e.g., Marketing, Engineering)*")
        email = st.text_input("Email*")
        phone = st.text_input("Phone")
        location = st.text_input("Location (City/Country)")
        experience = st.number_input("Years of Experience", min_value=0)
        can_help = st.text_area("How can you help others?*")
        needs_help = st.text_area("What support do you need?")
        bio = st.text_area("Short Bio (Max 200 chars)", max_chars=200)
        
        if st.form_submit_button("Submit"):
            if not all([name, profession, expertise, email, can_help]):
                st.error("Please fill required fields (*)")
            else:
                conn = sqlite3.connect('karwan_tijarat.db')
                c = conn.cursor()
                member_id = str(uuid4())
                c.execute("INSERT INTO members VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                         (member_id, name, profession, expertise, email, phone, location,
                          experience, can_help, needs_help, bio, datetime.now()))
                conn.commit()
                st.success(f"Welcome to Karwan-e-Tijarat! Your ID: {member_id}")
                conn.close()

def search_members():
    st.header("🔍 Find Professionals")
    col1, col2 = st.columns(2)
    with col1:
        profession = st.text_input("Profession (e.g., Engineer)")
    with col2:
        location = st.text_input("Location (e.g., Karachi)")
    
    expertise = st.text_input("Expertise (e.g., Digital Marketing)")
    
    if st.button("Search"):
        conn = sqlite3.connect('karwan_tijarat.db')
        c = conn.cursor()
        
        query = """SELECT full_name, profession, expertise, location, can_help 
                   FROM members 
                   WHERE profession LIKE ? OR location LIKE ? OR expertise LIKE ?"""
        params = (f"%{profession}%", f"%{location}%", f"%{expertise}%")
        
        c.execute(query, params)
        results = c.fetchall()
        
        if results:
            st.subheader(f"Found {len(results)} professionals:")
            for name, prof, exp, loc, help_txt in results:
                st.markdown(f"""
                **{name}**  
                *{prof}* | 📍 {loc}  
                **Skills:** {exp}  
                **Offers help with:** {help_txt}  
                ---
                """)
        else:
            st.warning("No matches found. Try different keywords.")
        conn.close()

# --- Main App ---
st.sidebar.title("Karwan-e-Tijarat")
menu = st.sidebar.radio("Menu", ["Join Us", "Find Professionals"])

if menu == "Join Us":
    register_member()
else:
    search_members()
