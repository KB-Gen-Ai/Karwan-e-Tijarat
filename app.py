import streamlit as st
import sqlite3
from fpdf import FPDF
from database import init_db, DB_PATH
from auth import check_login, auth_section

init_db()
check_login()

def generate_pdf(member_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add content
    pdf.cell(200, 10, txt="Karwan-e-Tijarat Profile", ln=True, align='C')
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
    
    return pdf.output(dest='S').encode('latin-1')

def profile_section():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM members WHERE email=?", (st.session_state.user_email,))
    data = c.fetchone()
    
    if data:
        with st.container():
            st.header("My Profile")
            
            name = st.text_input("Full Name", value=data[1])
            profession = st.text_input("Profession", value=data[2])
            expertise = st.text_input("Expertise", value=data[3])
            location = st.text_input("Location", value=data[6])
            experience = st.number_input("Experience (years)", value=data[7])
            bio = st.text_area("Bio", value=data[10], height=150)
            
            # Action buttons at bottom
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update Profile"):
                    c.execute("""UPDATE members SET
                        full_name=?, profession=?, expertise=?,
                        location=?, experience=?, bio=?
                        WHERE email=?""",
                        (name, profession, expertise, location,
                         experience, bio, st.session_state.user_email))
                    conn.commit()
                    st.success("Profile updated!")
            
            with col2:
                pdf_bytes = generate_pdf({
                    'full_name': name,
                    'profession': profession,
                    'expertise': expertise,
                    'location': location,
                    'experience': experience,
                    'bio': bio
                })
                st.download_button(
                    label="Download PDF Profile",
                    data=pdf_bytes,
                    file_name=f"profile_{name}.pdf",
                    mime="application/pdf"
                )
    conn.close()

def search_members():
    st.header("Find Professionals")
    search = st.text_input("Search by name, profession or location")
    if st.button("Search"):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""SELECT full_name, profession, expertise, location, email 
                   FROM members 
                   WHERE full_name LIKE ? OR profession LIKE ? OR location LIKE ?""",
                   (f"%{search}%", f"%{search}%", f"%{search}%"))
        results = c.fetchall()
        
        if results:
            for name, prof, exp, loc, email in results:
                st.write(f"**{name}** - {prof} ({loc})")
                st.write(f"Expertise: {exp}")
                with st.expander(f"Contact {name}"):
                    st.write(f"Email: {email}")
        conn.close()

if not st.session_state.logged_in:
    auth_section()
    st.stop()

st.sidebar.title("Menu")
page = st.sidebar.radio("Go to", ["My Profile", "Search"])

if page == "My Profile":
    profile_section()
else:
    search_members()
