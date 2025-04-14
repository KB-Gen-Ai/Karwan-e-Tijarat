import streamlit as st
import sqlite3
from datetime import datetime
from fpdf import FPDF
from database import init_db, DB_PATH
from auth import check_login, auth_section

init_db()
check_login()

def generate_pdf(member_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Karwan-e-Tijarat Profile", ln=True, align='C')
    
    fields = [
        ("Name", member_data.get('full_name', '')),
        ("Profession", member_data.get('profession', '')),
        ("Expertise", member_data.get('expertise', '')),
        ("Location", member_data.get('location', '')),
        ("Experience", f"{member_data.get('experience', 0)} years"),
        ("Bio", member_data.get('bio', ''))
    ]
    
    for label, value in fields:
        if value:
            pdf.cell(200, 10, txt=f"{label}: {value}", ln=True)
    
    return pdf.output()

def profile_section():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM members WHERE email=?", (st.session_state.user_email,))
    data = cursor.fetchone()
    
    if data:
        with st.form("Update Profile"):
            st.header("Your Profile")
            name = st.text_input("Full Name*", value=data[1])
            profession = st.text_input("Profession*", value=data[2])
            expertise = st.text_input("Expertise*", value=data[3])
            phone = st.text_input("Phone", value=data[5])
            location = st.text_input("Location", value=data[6])
            experience = st.number_input("Experience", value=data[7])
            can_help = st.text_area("How you can help*", value=data[8])
            needs_help = st.text_area("What help you need", value=data[9])
            bio = st.text_area("Bio", value=data[10])
            
            if st.form_submit_button("Update Profile"):
                cursor.execute("""UPDATE members SET
                    full_name=?, profession=?, expertise=?,
                    phone=?, location=?, experience=?,
                    can_help=?, needs_help=?, bio=?
                    WHERE email=?""",
                    (name, profession, expertise, phone, location,
                     experience, can_help, needs_help, bio,
                     st.session_state.user_email))
                conn.commit()
                st.success("Profile updated!")
                
                # Generate PDF after update
                member_data = {
                    'full_name': name,
                    'profession': profession,
                    'expertise': expertise,
                    'location': location,
                    'experience': experience,
                    'bio': bio
                }
                pdf_data = generate_pdf(member_data)
                st.download_button("Download Profile PDF", 
                                  data=pdf_data,
                                  file_name=f"KarwanProfile_{name}.pdf")
    conn.close()

def search_members():
    st.header("🔍 Find Professionals")
    search_term = st.text_input("Search by profession, expertise or location")
    if st.button("Search"):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""SELECT full_name, profession, expertise, location, can_help, email 
                       FROM members 
                       WHERE profession LIKE ? OR expertise LIKE ? OR location LIKE ?""",
                       (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        results = cursor.fetchall()
        
        if results:
            for name, prof, exp, loc, help_txt, email in results:
                st.markdown(f"""
                **{name}**  
                *{prof}* | 📍 {loc}  
                **Skills:** {exp}  
                **Offers help with:** {help_txt}  
                """)
                with st.expander(f"Contact {name}"):
                    st.markdown(f"**Email:** `{email}`")
        else:
            st.warning("No professionals found")
        conn.close()

if not st.session_state.logged_in:
    auth_section()
    st.stop()

st.sidebar.title("Karwan-e-Tijarat")
menu = st.sidebar.radio("Menu", ["Profile", "Find Professionals"])

if menu == "Profile":
    profile_section()
else:
    search_members()
