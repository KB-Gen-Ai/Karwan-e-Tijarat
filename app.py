import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import qrcode
from datetime import datetime

# Initialize database
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

init_db()

# --- PDF Generator (using ReportLab) ---
def generate_pdf(profile_data):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Header
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(300, 750, "Karwan-e-Tijarat Profile")
    p.line(50, 740, 550, 740)
    
    # Profile Data
    p.setFont("Helvetica", 12)
    y_position = 700
    fields = [
        ("Name", profile_data['full_name']),
        ("Email", profile_data['email']),
        ("Phone", profile_data['phone']),
        ("Profession", profile_data['profession']),
        ("Expertise", profile_data['expertise']),
        ("How I Can Help", profile_data['how_to_help'])
    ]
    
    for label, value in fields:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y_position, f"{label}:")
        p.setFont("Helvetica", 12)
        p.drawString(200, y_position, str(value))
        y_position -= 30
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

# --- QR Code Generator ---
def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()

# --- Streamlit UI ---
st.set_page_config(page_title="Karwan-e-Tijarat", layout="centered")
st.title("🌍 Karwan-e-Tijarat")
st.markdown("Professional Network for National Brand Building")
st.divider()

# --- Profile Form ---
with st.form("profile_form"):
    st.subheader("📝 Your Profile")
    
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    profession = st.text_input("Profession")
    expertise = st.text_area("Areas of Expertise")
    how_to_help = st.text_area("How You Can Help Others")
    
    submitted = st.form_submit_button("Save Profile")

if submitted:
    profile_id = str(datetime.now().timestamp())
    profile_data = {
        'id': profile_id,
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'profession': profession,
        'expertise': expertise,
        'how_to_help': how_to_help
    }
    
    # Save to DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO members 
                 (id, full_name, email, phone, profession, expertise, how_to_help) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (profile_id, full_name, email, phone, profession, expertise, how_to_help))
    conn.commit()
    conn.close()
    
    st.success("Profile saved successfully!")
    
    # Generate shareable link
    profile_url = f"{st.experimental_get_query_params().get('_', [''])[0]}?profile_id={profile_id}"
    qr_img = generate_qr_code(profile_url)
    
    col1, col2 = st.columns(2)
    with col1:
        st.image(qr_img, caption="Scan to share", width=200)
    with col2:
        st.write("**Shareable Link:**")
        st.code(profile_url)
    
    # PDF Download
    pdf_bytes = generate_pdf(profile_data)
    st.download_button(
        "📄 Download Profile PDF",
        data=pdf_bytes,
        file_name=f"{full_name}_profile.pdf",
        mime="application/pdf"
    )

# --- Search Functionality ---
st.divider()
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
        st.write(f"Found {len(results)} professionals:")
        for name, prof, exp, email, phone in results:
            with st.expander(f"{name} - {prof}"):
                st.write(f"**Expertise:** {exp}")
                st.write(f"**Contact:** {email} | {phone}")
    else:
        st.warning("No matching profiles found")
    conn.close()
