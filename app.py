import streamlit as st
import sqlite3
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import qrcode
from datetime import datetime
import re
import pandas as pd
import base64
from PIL import Image

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
                  linkedin_url TEXT,
                  social_media TEXT,
                  photo BLOB,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

def validate_email(email):
    """Basic email validation"""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validate_url(url):
    """Basic URL validation"""
    if not url:
        return True
    return re.match(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+", url)

def generate_pdf(profile_data, qr_img_bytes, photo_bytes=None):
    """Generate PDF with QR code and photo"""
    try:
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Header
        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(300, 780, "Karwan-e-Tijarat Profile")
        p.line(50, 770, 550, 770)
        
        # Add Photo to PDF if available
        if photo_bytes:
            try:
                photo_img = ImageReader(BytesIO(photo_bytes))
                p.drawImage(photo_img, 80, 650, width=100, height=100)
            except:
                pass
        
        # Add QR code to PDF
        if qr_img_bytes:
            qr_img = ImageReader(BytesIO(qr_img_bytes))
            p.drawImage(qr_img, 400, 650, width=120, height=120)
        
        # Profile Data
        p.setFont("Helvetica", 12)
        y_position = 700
        fields = [
            ("Name", profile_data.get('full_name', '')),
            ("Email", profile_data.get('email', '')),
            ("Phone", profile_data.get('phone', '')),
            ("Profession", profile_data.get('profession', '')),
            ("Expertise", profile_data.get('expertise', '')),
            ("How I Can Help", profile_data.get('how_to_help', '')),
            ("LinkedIn", profile_data.get('linkedin_url', '')),
            ("Social Media", profile_data.get('social_media', ''))
        ]
        
        for label, value in fields:
            if value:  # Only show fields with values
                p.setFont("Helvetica-Bold", 12)
                p.drawString(80, y_position, f"{label}:")
                p.setFont("Helvetica", 12)
                p.drawString(180, y_position, str(value))
                y_position -= 25
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")
        return None

def generate_qr_code(url):
    """Generate QR code with logo"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf)
        return buf.getvalue()
    except Exception as e:
        st.error(f"QR code generation failed: {str(e)}")
        return None

def check_email_exists(email):
    """Check if email already exists in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM members WHERE email=?", (email,))
        return c.fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def get_profile_by_email(email):
    """Get profile by email"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM members WHERE email=?", (email,))
        columns = [column[0] for column in c.description]
        result = c.fetchone()
        if result:
            return dict(zip(columns, result))
        return None
    except sqlite3.Error:
        return None
    finally:
        conn.close()

def get_all_profiles():
    """Get all profiles for admin export"""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM members", conn)
        return df
    except sqlite3.Error:
        return None
    finally:
        conn.close()

# --- Streamlit UI ---
st.set_page_config(page_title="Karwan-e-Tijarat", layout="centered")
st.title("🌍 Karwan-e-Tijarat")
st.markdown("National Brand Building by helping Pakistanis connect, collaborate, and grow globally")
st.divider()

# Admin Section
if st.secrets.get("ADMIN_PASSWORD"):
    admin_expander = st.expander("Admin Tools")
    with admin_expander:
        admin_pass = st.text_input("Enter Admin Password", type="password")
        if admin_pass == st.secrets["ADMIN_PASSWORD"]:
            st.success("Admin access granted")
            if st.button("Export All Data to CSV"):
                df = get_all_profiles()
                if df is not None:
                    csv = df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    st.markdown(
                        f'<a href="data:file/csv;base64,{b64}" download="karwan_tijarat_profiles.csv">Download CSV File</a>',
                        unsafe_allow_html=True
                    )
                else:
                    st.error("Failed to export data")

# Profile Management Section
st.subheader("👤 Profile Management")
profile_mode = st.radio("Select Mode", ["Create New Profile", "Update Existing Profile"])

if profile_mode == "Update Existing Profile":
    update_email = st.text_input("Enter your registered email to load profile")
    if st.button("Load Profile"):
        profile_data = get_profile_by_email(update_email)
        if profile_data:
            st.session_state.profile_data = profile_data
            st.success("Profile loaded successfully!")
        else:
            st.error("No profile found with this email")

# --- Profile Form ---
with st.form("profile_form"):
    st.subheader("📝 Your Profile")
    
    # Check for existing profile data
    profile_data = st.session_state.get('profile_data', {})
    
    # Personal Info
    full_name = st.text_input("Full Name*", value=profile_data.get('full_name', ''), key="full_name")
    email = st.text_input("Email*", value=profile_data.get('email', ''), key="email")
    
    # Email validation (immediate feedback)
    if email:
        if not validate_email(email):
            st.warning("Please enter a valid email address")
        elif check_email_exists(email) and profile_mode == "Create New Profile":
            st.warning("This email is already registered. Please use 'Update Existing Profile' mode.")
    
    phone = st.text_input("Phone", value=profile_data.get('phone', ''), key="phone")
    
    # Photo Upload
    photo = st.file_uploader("Upload Profile Photo", type=['jpg', 'jpeg', 'png'])
    
    # Professional Info
    profession = st.text_input("Profession*", value=profile_data.get('profession', ''), key="profession")
    expertise = st.text_area("Areas of Expertise*", value=profile_data.get('expertise', ''), key="expertise")
    how_to_help = st.text_area("How You Can Help Others*", value=profile_data.get('how_to_help', ''), key="how_to_help")
    
    # Social Media
    linkedin_url = st.text_input("LinkedIn Profile URL", value=profile_data.get('linkedin_url', ''), key="linkedin_url")
    social_media = st.text_input("Other Social Media Profile", value=profile_data.get('social_media', ''), key="social_media")
    
    submitted = st.form_submit_button("Save Profile")
    st.markdown("*Required fields")

if submitted:
    # Validate inputs
    errors = []
    if not full_name:
        errors.append("Full name is required")
    if not email or not validate_email(email):
        errors.append("Valid email is required")
    if not profession:
        errors.append("Profession is required")
    if linkedin_url and not validate_url(linkedin_url):
        errors.append("Enter a valid LinkedIn URL")
    if social_media and not validate_url(social_media):
        errors.append("Enter a valid social media URL")
    
    # Check for duplicate email in create mode
    if profile_mode == "Create New Profile" and check_email_exists(email):
        errors.append("This email is already registered. Please use 'Update Existing Profile' mode.")
    
    if errors:
        for error in errors:
            st.error(error)
    else:
        try:
            # Prepare profile data
            profile_id = profile_data.get('id', str(datetime.now().timestamp()))
            profile_data = {
                'id': profile_id,
                'full_name': full_name,
                'email': email,
                'phone': phone,
                'profession': profession,
                'expertise': expertise,
                'how_to_help': how_to_help,
                'linkedin_url': linkedin_url,
                'social_media': social_media,
                'photo': photo.read() if photo else None
            }
            
            # Save to DB
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO members 
                         (id, full_name, email, phone, profession, expertise, 
                          how_to_help, linkedin_url, social_media, photo) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (profile_id, full_name, email, phone, profession,
                       expertise, how_to_help, linkedin_url, social_media, 
                       profile_data['photo']))
            conn.commit()
            
            st.success("Profile saved successfully!")
            st.session_state.current_profile_id = profile_id
            
            # Generate shareable link
            base_url = st.experimental_get_query_params().get('_', [''])[0]
            profile_url = f"{base_url}?profile_id={profile_id}"
            qr_img = generate_qr_code(profile_url)
            
            if qr_img:
                col1, col2 = st.columns(2)
                with col1:
                    st.image(qr_img, caption="Scan to share", width=200)
                    if photo:
                        st.image(photo, caption="Your Profile Photo", width=200)
                with col2:
                    st.write("**Shareable Link:**")
                    st.markdown(f"[{profile_url}]({profile_url})")
                    st.code(profile_url)
            
            # PDF Download
            if qr_img:
                pdf_bytes = generate_pdf(profile_data, qr_img, photo_bytes=profile_data['photo'])
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
        finally:
            conn.close()

# --- Search Functionality ---
st.divider()
st.subheader("🔍 Search Professionals")

search_term = st.text_input("Search by name, profession or expertise", key="search")
if st.button("Search", key="search_button"):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""SELECT full_name, profession, expertise, email, phone, 
                      linkedin_url, social_media 
                   FROM members 
                   WHERE full_name LIKE ? OR profession LIKE ? OR expertise LIKE ?""",
                   (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        results = c.fetchall()
        
        if results:
            st.write(f"Found {len(results)} professionals:")
            for name, prof, exp, email, phone, linkedin, social in results:
                with st.expander(f"{name} - {prof}"):
                    st.write(f"**Expertise:** {exp}")
                    st.write(f"**Email:** {email}")
                    st.write(f"**Phone:** {phone}")
                    if linkedin:
                        st.markdown(f"**LinkedIn:** [View Profile]({linkedin})")
                    if social:
                        st.markdown(f"**Social Media:** [View Profile]({social})")
        else:
            st.warning("No matching profiles found")
    except sqlite3.Error as e:
        st.error(f"Database error: {str(e)}")
    finally:
        conn.close()
