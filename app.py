import streamlit as st
import sqlite3
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

def generate_pdf(profile_data):
    """Generate PDF using ReportLab with error handling"""
    try:
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
            ("Name", profile_data.get('full_name', '')),
            ("Email", profile_data.get('email', '')),
            ("Phone", profile_data.get('phone', '')),
            ("Profession", profile_data.get('profession', '')),
            ("Expertise", profile_data.get('expertise', '')),
            ("How I Can Help", profile_data.get('how_to_help', ''))
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
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")
        return None

def generate_qr_code(url):
    """Generate QR code with error handling"""
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf)
        return buf.getvalue()
    except Exception as e:
        st.error(f"QR code generation failed: {str(e)}")
        return None

# --- Streamlit UI ---
st.set_page_config(page_title="Karwan-e-Tijarat", layout="centered")
st.title("🌍 Karwan-e-Tijarat")
st.markdown("National Brand Building by helping Pakistanis connect, collaborate, and grow globally")
st.divider()

# --- Profile Form ---
with st.form("profile_form"):
    st.subheader("📝 Your Profile")
    
    full_name = st.text_input("Full Name", key="full_name")
    email = st.text_input("Email", key="email")
    phone = st.text_input("Phone", key="phone")
    profession = st.text_input("Profession", key="profession")
    expertise = st.text_area("Areas of Expertise", key="expertise")
    how_to_help = st.text_area("How You Can Help Others", key="how_to_help")
    
    submitted = st.form_submit_button("Save Profile")

if submitted:
    # Validate required fields
    if not all([full_name, email, profession]):
        st.error("Please fill in all required fields (Name, Email, Profession)")
    else:
        try:
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
            profile_url = f"/?profile_id={profile_id}"
            qr_img = generate_qr_code(profile_url)
            
            if qr_img:
                col1, col2 = st.columns(2)
                with col1:
                    st.image(qr_img, caption="Scan to share", width=200)
                with col2:
                    st.write("**Shareable Link:**")
                    st.code(profile_url)
            
            # PDF Download
            pdf_bytes = generate_pdf(profile_data)
            if pdf_bytes:
                st.download_button(
                    "📄 Download Profile PDF",
                    data=pdf_bytes,
                    file_name=f"{full_name}_profile.pdf",
                    mime="application/pdf"
                )
                
        except sqlite3.Error as e:
            st.error(f"Database error: {str(e)}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

# --- Search Functionality ---
st.divider()
st.subheader("🔍 Search Professionals")

search_term = st.text_input("Search by name, profession or expertise", key="search")
if st.button("Search", key="search_button"):
    try:
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
    except sqlite3.Error as e:
        st.error(f"Database error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()
