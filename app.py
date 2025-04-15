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
    """Initialize database with fresh schema"""
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
    """Basic email validation"""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def get_country_code(country_name):
    """Get country phone code"""
    try:
        country = pycountry.countries.get(name=country_name)
        return f"+{country.numeric_phone_code}"
    except:
        return "+92"  # Default to Pakistan

def format_phone(phone_str, country_name):
    """Format phone number with country code"""
    if not phone_str:
        return None
    try:
        country_code = get_country_code(country_name)
        if not phone_str.startswith('+'):
            phone_str = f"{country_code}{phone_str.lstrip('0')}"
        parsed = phonenumbers.parse(phone_str, None)
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except NumberParseException:
        return phone_str

def generate_pdf(profile_data, qr_img_bytes):
    """Generate PDF with QR code"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Header
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(300, 780, "Karwan-e-Tijarat Profile")
    p.line(50, 770, 550, 770)
    
    # Add QR code
    if qr_img_bytes:
        qr_img = ImageReader(BytesIO(qr_img_bytes))
        p.drawImage(qr_img, 400, 650, width=120, height=120)
    
    # Profile Data
    p.setFont("Helvetica", 12)
    y_position = 700
    fields = [
        ("Name", profile_data.get('full_name', '')),
        ("Email", profile_data.get('email', '')),
        ("Location", f"{profile_data.get('city', '')}, {profile_data.get('country', '')}"),
        ("Primary Phone", profile_data.get('primary_phone', '')),
        ("Secondary Phone", profile_data.get('secondary_phone', '')),
        ("Profession", profile_data.get('profession', '')),
        ("Expertise", profile_data.get('expertise', '')),
        ("How I Can Help", profile_data.get('how_to_help', '')),
        ("Business URL", profile_data.get('business_url', ''))
    ]
    
    for label, value in fields:
        if value:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(80, y_position, f"{label}:")
            p.setFont("Helvetica", 12)
            p.drawString(180, y_position, str(value))
            y_position -= 25
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

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
        st.error(f"QR generation failed: {e}")
        return None

def check_email_exists(email):
    """Check if email exists"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM members WHERE email=?", (email,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def get_profile_by_email(email):
    """Load profile by email"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM members WHERE email=?", (email,))
    profile = c.fetchone()
    conn.close()
    return dict(profile) if profile else None

def save_profile(profile_data):
    """Save profile to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO members 
                    (id, full_name, email, city, country, 
                     primary_phone, secondary_phone, profession, 
                     expertise, how_to_help, business_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (profile_data['id'], profile_data['full_name'],
                  profile_data['email'], profile_data['city'],
                  profile_data['country'], profile_data['primary_phone'],
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
    """Get all profiles for admin export"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM members", conn)
    conn.close()
    return df

# --- Streamlit UI ---
st.set_page_config(page_title="Karwan-e-Tijarat", layout="centered")
st.title("🌍 Karwan-e-Tijarat")

# Profile Mode
profile_mode = st.radio("Mode", ["Create New", "Update Existing"], horizontal=True)
profile_data = {}
if profile_mode == "Update Existing":
    update_email = st.text_input("Enter registered email to load profile")
    if st.button("Load Profile"):
        profile_data = get_profile_by_email(update_email)
        if profile_data:
            st.success("Profile loaded!")
        else:
            st.error("Profile not found")

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
        default_country = profile_data.get('country', 'Pakistan')
        country_idx = country_list.index(default_country) if default_country in country_list else country_list.index("Pakistan")
        country = st.selectbox("Country", country_list, index=country_idx)
    
    # Phone Fields
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
    
    # Optional URL
    business_url = st.text_input("Business/Social Media URL",
                               value=profile_data.get('business_url', ''),
                               placeholder="https://example.com (optional)")
    
    submitted = st.form_submit_button("Save Profile")
    st.markdown("*Required fields")

if submitted:
    errors = []
    if not all([full_name, email, primary_phone, profession, expertise, how_to_help]):
        errors.append("Missing required fields")
    elif not validate_email(email):
        errors.append("Invalid email format")
    elif check_email_exists(email) and profile_mode == "Create New":
        errors.append("Email already registered")
    
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
            st.success("Profile saved successfully!")
            
            # Generate shareable link
            base_url = st.experimental_get_query_params().get('_', [''])[0]
            profile_url = f"{base_url}?profile_id={profile_data['id']}"
            qr_img = generate_qr_code(profile_url)
            
            if qr_img:
                col1, col2 = st.columns(2)
                with col1:
                    st.image(qr_img, caption="Scan to share", width=200)
                with col2:
                    st.write("**Shareable Link:**")
                    st.markdown(f"[{profile_url}]({profile_url})")
                    st.code(profile_url)
                
                # PDF Download
                pdf_bytes = generate_pdf(profile_data, qr_img)
                if pdf_bytes:
                    st.download_button(
                        "📄 Download Profile PDF",
                        data=pdf_bytes,
                        file_name=f"{full_name}_profile.pdf",
                        mime="application/pdf"
                    )

# Admin Export
if st.secrets.get("ADMIN_PASSWORD"):
    with st.expander("Admin Tools"):
        admin_pass = st.text_input("Enter Admin Password", type="password")
        if admin_pass == st.secrets["ADMIN_PASSWORD"]:
            if st.button("Export All Data to CSV"):
                df = get_all_profiles()
                if df is not None:
                    csv = df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    st.markdown(
                        f'<a href="data:file/csv;base64,{b64}" download="karwan_profiles.csv">Download CSV</a>',
                        unsafe_allow_html=True
                    )

# Search Functionality
st.divider()
st.subheader("🔍 Search Professionals")
search_term = st.text_input("Search by name, profession or expertise")
if st.button("Search"):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""SELECT full_name, profession, expertise, email, 
                      primary_phone, city, country 
                   FROM members 
                   WHERE full_name LIKE ? OR profession LIKE ? OR expertise LIKE ?""",
                   (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        results = c.fetchall()
        
        if results:
            st.write(f"Found {len(results)} professionals:")
            for name, prof, exp, email, phone, city, country in results:
                with st.expander(f"{name} - {prof}"):
                    st.write(f"**Location:** {city}, {country}")
                    st.write(f"**Expertise:** {exp}")
                    st.write(f"**Email:** {email}")
                    st.write(f"**Phone:** {phone}")
        else:
            st.warning("No matching profiles found")
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    finally:
        conn.close()
