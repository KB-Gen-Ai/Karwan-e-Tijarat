import streamlit as st
import sqlite3
import os
from datetime import datetime
from fpdf import FPDF
from database import init_db, DB_PATH
from auth import check_login, login_form

# Initialize database and auth
init_db()
check_login()

# PDF Generator
def generate_pdf(member_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Karwan-e-Tijarat Profile", ln=True, align='C')
    pdf.ln(10)
    fields = [
        ("Name", member_data['full_name']),
        ("Profession", member_data['profession']),
        ("Expertise", member_data['expertise']),
        ("Location", member_data['location']),
        ("Experience", f"{member_data['experience']} years"),
        ("Bio", member_data['bio'])
    ]
    for label, value in fields:
        pdf.cell(200, 10, txt=f"{label}: {value}", ln=True)
    return pdf.output(dest='S').encode('latin1')

# Simplified ID Generator
def generate_simple_id(name, city):
    city_part = city[:3].upper() if city else "GEN"
    name_part = name[:3].upper()
    serial = datetime.now().strftime("%H%M%S")
    return f"{city_part}{name_part}{serial}"

# Registration Form
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
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                member_id = generate_simple_id(name, location)
                try:
                    c.execute("INSERT INTO members VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                             (member_id, name, profession, expertise, email, phone,
                              location, experience, can_help, needs_help, bio, datetime.now()))
                    conn.commit()
                    
                    # Generate and offer PDF download
                    member_data = {
                        'full_name': name,
                        'profession': profession,
                        'expertise': expertise,
                        'location': location,
                        'experience': experience,
                        'bio': bio
                    }
                    pdf_data = generate_pdf(member_data)
                    st.success("Registration successful!")
                    st.download_button("Download Profile PDF", 
                                      data=pdf_data, 
                                      file_name=f"KarwanProfile_{member_id}.pdf")
                except sqlite3.IntegrityError:
                    st.error("This email is already registered!")
                finally:
                    conn.close()

# Search Functionality
def search_members():
    st.header("🔍 Find Professionals")
    col1, col2 = st.columns(2)
    with col1:
        profession = st.text_input("Profession (e.g., Engineer)")
    with col2:
        location = st.text_input("Location (e.g., Karachi)")
    expertise = st.text_input("Expertise (e.g., Digital Marketing)")
    
    if st.button("Search"):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        query = """SELECT full_name, profession, expertise, location, can_help, email 
                   FROM members 
                   WHERE profession LIKE ? OR location LIKE ? OR expertise LIKE ?"""
        params = (f"%{profession}%", f"%{location}%", f"%{expertise}%")
        
        c.execute(query, params)
        results = c.fetchall()
        
        if results:
            st.subheader(f"Found {len(results)} professionals:")
            for idx, (name, prof, exp, loc, help_txt, email) in enumerate(results, 1):
                st.markdown(f"""
                **{name}**  
                *{prof}* | 📍 {loc}  
                **Skills:** {exp}  
                **Offers help with:** {help_txt}  
                """)
                
                with st.expander(f"Contact {name}"):
                    st.markdown(f"**Email:** `{email}`")
                    if st.button("Copy Email", key=f"email_{idx}"):
                        st.session_state.copied = email
                        st.rerun()
                
                st.markdown("---")
        else:
            st.warning("No matches found. Try different keywords.")
        conn.close()

# Main App Flow
if not st.session_state.logged_in:
    login_form()
    st.stop()

st.sidebar.title("Karwan-e-Tijarat")
menu = st.sidebar.radio("Menu", ["Join Us", "Find Professionals"])

if menu == "Join Us":
    register_member()
else:
    search_members()
