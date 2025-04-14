import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import qrcode
from datetime import datetime

# Initialize database (without auth)
DB_PATH = "karwan_tijarat.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS members
                 (id TEXT PRIMARY KEY,
                  full_name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  phone TEXT,
                  profession TEXT NOT NULL,
                  expertise TEXT NOT NULL,
                  how_to_help TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Initialize DB
init_db()

# --- Main App ---
st.set_page_config(page_title="Karwan-e-Tijarat", layout="centered")
st.markdown("<h1 style='text-align: center;'>🌍 Karwan-e-Tijarat</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Professional Network for National Brand Building</p>", unsafe_allow_html=True)
st.markdown("---")

# --- Profile Management ---
def save_profile(profile_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO members 
                 (id, full_name, email, phone, profession, expertise, how_to_help) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (profile_data['id'],
               profile_data['full_name'],
               profile_data['email'],
               profile_data['phone'],
               profile_data['profession'],
               profile_data['expertise'],
               profile_data['how_to_help']))
    conn.commit()
    conn.close()

def get_profile_by_id(profile_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM members WHERE id=?", (profile_id,))
    result = c.fetchone()
    conn.close()
    return result

def generate_pdf(profile_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Karwan-e-Tijarat Profile", ln=1, align='C')
    
    fields = [
        ("Name", profile_data[1]),
        ("Email", profile_data[2]),
        ("Phone", profile_data[3]),
        ("Profession", profile_data[4]),
        ("Expertise", profile_data[5]),
        ("How I Can Help", profile_data[6])
    ]
    
    for label, value in fields:
        pdf.cell(200, 10, txt=f"{label}: {value}", ln=1)
    
    return pdf.output(dest='S').encode('latin1')

def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()

# --- Main Profile Form ---
with st.form("profile_form"):
    st.subheader("📝 Create/Update Your Profile")
    
    full_name = st.text_input("👤 Full Name")
    email = st.text_input("📧 Email")
    phone = st.text_input("📱 Phone")
    profession = st.text_input("💼 Profession")
    expertise = st.text_area("📚 Expertise")
    how_to_help = st.text_area("🤝 How You Can Help Others")
    
    submitted = st.form_submit_button("💾 Save Profile")

if submitted:
    profile_id = str(datetime.now().timestamp())  # Simple ID generation
    profile_data = {
        'id': profile_id,
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'profession': profession,
        'expertise': expertise,
        'how_to_help': how_to_help
    }
    
    save_profile(profile_data)
    st.success("Profile saved successfully!")
    
    # Generate shareable link
    profile_url = f"?profile_id={profile_id}"
    qr_img = generate_qr_code(profile_url)
    
    st.image(qr_img, caption="Scan to share your profile", width=200)
    st.markdown(f"**Shareable link:** `{profile_url}`")
    
    # PDF Download
    pdf_bytes = generate_pdf(get_profile_by_id(profile_id))
    st.download_button(
        "📄 Download Profile PDF",
        data=pdf_bytes,
        file_name=f"{full_name}_profile.pdf",
        mime="application/pdf"
    )

# --- Search Functionality ---
st.markdown("---")
st.subheader("🔍 Search Professionals")

search_term = st.text_input("Search by name, profession or expertise")
if st.button("Search"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT full_name, profession, expertise, email, phone 
               FROM members 
               WHERE full_name LIKE ? OR profession LIKE ? OR expertise LIKE ?""",
               (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
    results = c.fetchall()
    
    if results:
        for name, prof, exp, email, phone in results:
            with st.expander(f"{name} - {prof}"):
                st.write(f"**Expertise:** {exp}")
                st.write(f"**Contact:** {email} | {phone}")
    else:
        st.warning("No matching profiles found")
    conn.close()
