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
import phonenumbers
from phonenumbers import NumberParseException
import pycountry

# Initialize database
DB_PATH = "karwan_tijarat.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS members
                 (id TEXT PRIMARY KEY,
                  full_name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  city TEXT,
                  country TEXT,
                  primary_phone TEXT,
                  secondary_phone TEXT,
                  profession TEXT NOT NULL,
                  expertise TEXT NOT NULL,
                  how_to_help TEXT NOT NULL,
                  business_url TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def get_country_code(country_name):
    try:
        return f"+{pycountry.countries.get(name=country_name).numeric_phone_code}"
    except:
        return "+92"

def format_phone(phone_str, country_name):
    if not phone_str: return None
    try:
        country_code = get_country_code(country_name)
        if not phone_str.startswith('+'):
            phone_str = f"{country_code}{phone_str.lstrip('0')}"
        parsed = phonenumbers.parse(phone_str, None)
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except NumberParseException:
        return phone_str

def generate_pdf(profile_data, qr_img_bytes):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(300, 780, "Karwan-e-Tijarat Profile")
    p.line(50, 770, 550, 770)
    if qr_img_bytes:
        p.drawImage(ImageReader(BytesIO(qr_img_bytes)), 400, 650, width=120, height=120)
    p.setFont("Helvetica", 12)
    y = 700
    for label, value in [
        ("Name", profile_data.get('full_name', '')),
        ("Email", profile_data.get('email', '')),
        ("Location", f"{profile_data.get('city', '')}, {profile_data.get('country', '')}"),
        ("Primary Phone", profile_data.get('primary_phone', '')),
        ("Secondary Phone", profile_data.get('secondary_phone', '')),
        ("Profession", profile_data.get('profession', '')),
        ("Expertise", profile_data.get('expertise', '')),
        ("How I Can Help", profile_data.get('how_to_help', '')),
        ("Business URL", profile_data.get('business_url', ''))
    ]:
        if value:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(80, y, f"{label}:")
            p.setFont("Helvetica", 12)
            p.drawString(180, y, str(value))
            y -= 25
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

def generate_qr_code(url):
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf)
        return buf.getvalue()
    except Exception as e:
        st.error(f"QR generation failed: {e}")
        return None

def check_email_exists(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM members WHERE email=?", (email,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def get_profile_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM members WHERE email=?", (email,))
    profile = c.fetchone()
    conn.close()
    return dict(profile) if profile else None

def save_profile(profile_data):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO members 
                    (id, full_name, email, city, country, primary_phone, 
                     secondary_phone, profession, expertise, how_to_help, business_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (profile_data['id'], profile_data['full_name'], profile_data['email'],
                  profile_data['city'], profile_data['country'], profile_data['primary_phone'],
                  profile_data.get('secondary_phone'), profile_data['profession'],
                  profile_data['expertise'], profile_data['how_to_help'],
                  profile_data.get('business_url')))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        conn.close()

def get_all_profiles():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM members", conn)
    conn.close()
    return df

# --- UI ---
st.set_page_config(page_title="Karwan-e-Tijarat", layout="centered")
st.title("🌍 Karwan-e-Tijarat")

# Profile Mode
mode = st.radio("Profile Mode", ["Create New", "Update Existing"], horizontal=True)
profile_data = {}

if mode == "Update Existing":
    email_to_update = st.text_input("Enter your registered email")
    if st.button("Load Profile"):
        profile_data = get_profile_by_email(email_to_update)
        if profile_data:
            st.success("Profile loaded!")
        else:
            st.error("No profile found with this email")

with st.form("profile_form"):
    # Personal Info
    full_name = st.text_input("Full Name*", value=profile_data.get('full_name', ''))
    email = st.text_input("Email*", value=profile_data.get('email', ''))
    
    # Location
    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("City", value=profile_data.get('city', ''), placeholder="e.g. Karachi")
    with col2:
        country_list = [c.name for c in pycountry.countries]
        default_idx = country_list.index(profile_data.get('country', 'Pakistan'))
        country = st.selectbox("Country", country_list, index=default_idx)
    
    # Phone
    country_code = get_country_code(country)
    primary_phone = st.text_input("Primary Phone*", 
                                value=profile_data.get('primary_phone', ''),
                                placeholder=f"{country_code}XXXXXXXXXX")
    secondary_phone = st.text_input("Secondary Phone", 
                                  value=profile_data.get('secondary_phone', ''),
                                  placeholder="Optional")

    # Professional Info
    profession = st.text_input("Profession*", value=profile_data.get('profession', ''))
    expertise = st.text_area("Expertise*", value=profile_data.get('expertise', ''))
    how_to_help = st.text_area("How You Can Help*", value=profile_data.get('how_to_help', ''))
    business_url = st.text_input("Business URL", value=profile_data.get('business_url', ''),
                               placeholder="https://example.com (optional)")
    
    submitted = st.form_submit_button("Save Profile")

if submitted:
    errors = []
    if not all([full_name, email, primary_phone, profession, expertise, how_to_help]):
        errors.append("Missing required fields")
    elif not validate_email(email):
        errors.append("Invalid email format")
    elif mode == "Create New" and check_email_exists(email):
        errors.append("Email already exists (use Update mode)")
    
    if errors:
        for error in errors:
            st.error(error)
    else:
        profile_data = {
            'id': profile_data.get('id', str(datetime.now().timestamp())),
            'full_name': full_name,
            'email': email,
            'city': city,
            'country': country,
            'primary_phone': format_phone(primary_phone, country),
            'secondary_phone': format_phone(secondary_phone, country) if secondary_phone else None,
            'profession': profession,
            'expertise': expertise,
            'how_to_help': how_to_help,
            'business_url': business_url or None
        }
        
        if save_profile(profile_data):
            st.success("Profile saved!")
            # [Keep QR/PDF generation code from previous version]

# [Keep Admin Export and Search functionality exactly as before]
