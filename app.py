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
import phonenumbers
from phonenumbers import NumberParseException

# Initialize database
DB_PATH = "karwan_tijarat.db"

def init_db():
    """Initialize database with fresh schema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Drop existing table if exists
        c.execute("DROP TABLE IF EXISTS members")
        
        # Create fresh table with all columns
        c.execute('''CREATE TABLE members
                     (id TEXT PRIMARY KEY,
                      full_name TEXT NOT NULL,
                      email TEXT UNIQUE NOT NULL,
                      primary_phone TEXT,
                      secondary_phone TEXT,
                      profession TEXT NOT NULL,
                      expertise TEXT NOT NULL,
                      how_to_help TEXT NOT NULL,
                      business_url TEXT,
                      social_media_url TEXT,
                      photo BLOB,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database initialization failed: {str(e)}")
    finally:
        conn.close()

init_db()

def validate_email(email):
    """Basic email validation"""
    if not email:
        return False
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def format_phone_number(phone):
    """Format phone number if valid"""
    if not phone:
        return None
    try:
        parsed = phonenumbers.parse(phone, "PK")  # Default to Pakistan if no country code
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed, 
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
        return phone  # Return original if not valid
    except NumberParseException:
        return phone  # Return original if can't parse

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
            ("Primary Phone", profile_data.get('primary_phone', '')),
            ("Secondary Phone", profile_data.get('secondary_phone', '')),
            ("Profession", profile_data.get('profession', '')),
            ("Expertise", profile_data.get('expertise', '')),
            ("How I Can Help", profile_data.get('how_to_help', '')),
            ("Business URL", profile_data.get('business_url', '')),
            ("Social Media", profile_data.get('social_media_url', ''))
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
    """Generate QR code"""
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
    """Check if email exists in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM members WHERE email=?", (email,))
        return c.fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def save_profile(profile_data):
    """Save profile to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''INSERT OR REPLACE INTO members 
                     (id, full_name, email, primary_phone, secondary_phone, 
                      profession, expertise, how_to_help, business_url, 
                      social_media_url, photo) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (profile_data['id'], profile_data['full_name'], 
                   profile_data['email'], profile_data['primary_phone'],
                   profile_data['secondary_phone'], profile_data['profession'],
                   profile_data['expertise'], profile_data['how_to_help'],
                   profile_data['business_url'], profile_data['social_media_url'],
                   profile_data.get('photo')))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {str(e)}")
        return False
    finally:
        conn.close()

# --- Streamlit UI ---
st.set_page_config(page_title="Karwan-e-Tijarat", layout="centered")
st.title("🌍 Karwan-e-Tijarat")
st.markdown("National Brand Building by helping Pakistanis connect, collaborate, and grow globally")
st.divider()

# --- Profile Form ---
with st.form("profile_form"):
    st.subheader("📝 Your Profile")
    
    # Personal Info
    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Full Name*")
    with col2:
        email = st.text_input("Email*")
    
    # Phone Numbers
    col1, col2 = st.columns(2)
    with col1:
        primary_phone = st.text_input("Primary Phone*", 
                                    help="Format: +923001234567 or 03001234567")
    with col2:
        secondary_phone = st.text_input("Secondary Phone (Optional)",
                                      help="Format: +923001234567 or 03001234567")
    
    # Photo Upload
    photo = st.file_uploader("Profile Photo (Optional)", 
                           type=['jpg', 'jpeg', 'png'])
    
    # Professional Info
    profession = st.text_input("Profession*")
    expertise = st.text_area("Areas of Expertise*", 
                           help="List your key skills and expertise areas")
    how_to_help = st.text_area("How You Can Help Others*", 
                             help="Describe how you can contribute to the community")
    
    # URL Fields
    business_url = st.text_input("Business/Website URL (Optional)",
                               placeholder="https://yourbusiness.com")
    social_media_url = st.text_input("Social Media Profile (Optional)",
                                   placeholder="https://linkedin.com/in/yourprofile")
    
    submitted = st.form_submit_button("Save Profile")
    st.markdown("*Required fields")

if submitted:
    # Validate required fields
    errors = []
    if not full_name:
        errors.append("Full name is required")
    if not email or not validate_email(email):
        errors.append("Valid email is required")
    if not primary_phone:
        errors.append("Primary phone is required")
    if not profession:
        errors.append("Profession is required")
    if not expertise:
        errors.append("Areas of expertise are required")
    if not how_to_help:
        errors.append("Please specify how you can help others")
    
    # Check for duplicate email
    if email and check_email_exists(email):
        errors.append("This email is already registered")
    
    if errors:
        for error in errors:
            st.error(error)
    else:
        # Format phone numbers
        formatted_primary = format_phone_number(primary_phone)
        formatted_secondary = format_phone_number(secondary_phone) if secondary_phone else None
        
        profile_data = {
            'id': str(datetime.now().timestamp()),
            'full_name': full_name,
            'email': email,
            'primary_phone': formatted_primary,
            'secondary_phone': formatted_secondary,
            'profession': profession,
            'expertise': expertise,
            'how_to_help': how_to_help,
            'business_url': business_url if business_url else None,
            'social_media_url': social_media_url if social_media_url else None,
            'photo': photo.read() if photo else None
        }
        
        if save_profile(profile_data):
            st.success("Profile saved successfully!")
            
            # Generate shareable link
            base_url = st.experimental_get_query_params().get('_', [''])[0]
            profile_url = f"{base_url}?profile_id={profile_data['id']}"
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
                pdf_bytes = generate_pdf(profile_data, qr_img, 
                                        photo_bytes=profile_data['photo'])
                if pdf_bytes:
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
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""SELECT full_name, profession, expertise, email, 
                      primary_phone, business_url, social_media_url 
                   FROM members 
                   WHERE full_name LIKE ? OR profession LIKE ? OR expertise LIKE ?""",
                   (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        results = c.fetchall()
        
        if results:
            st.write(f"Found {len(results)} professionals:")
            for name, prof, exp, email, phone, business_url, social_url in results:
                with st.expander(f"{name} - {prof}"):
                    st.write(f"**Expertise:** {exp}")
                    st.write(f"**Email:** {email}")
                    st.write(f"**Phone:** {phone}")
                    if business_url:
                        st.markdown(f"**Business URL:** [Visit]({business_url})")
                    if social_url:
                        st.markdown(f"**Social Media:** [View Profile]({social_url})")
        else:
            st.warning("No matching profiles found")
    except sqlite3.Error as e:
        st.error(f"Database error: {str(e)}")
    finally:
        conn.close()
