import streamlit as st

# ✅ Must be the first Streamlit command
st.set_page_config(page_title="Karwan-e-Tijarat", layout="centered")

import sqlite3
from io import BytesIO
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import qrcode
import re
import pandas as pd
import base64
import phonenumbers
from phonenumbers import NumberParseException
import pycountry
from geopy.geocoders import Nominatim

from database import init_db, migrate_db, get_profile_by_id, get_profile_by_email, save_profile, get_all_profiles, search_profiles

DB_PATH = "karwan_tijarat.db"

# ✅ Initialize database with migrations
init_db()
migrate_db()

def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def get_country_phone_code(country_name):
    try:
        country = pycountry.countries.get(name=country_name)
        return f"+{phonenumbers.country_code_for_region(country.alpha_2)}"
    except:
        return "+92"  # Default to Pakistan

def format_phone(phone_str, country_name):
    if not phone_str: return ''
    try:
        country_code = get_country_phone_code(country_name)
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
        p.drawImage(ImageReader(BytesIO(qr_img_bytes)), 400, 600, width=120, height=120)
    
    y = 700
    line_spacing = 18
    p.setFont("Helvetica", 12)
    
    fields = [
        ("Name", profile_data.get('full_name', '')),
        ("Email", profile_data.get('email', '')),
        ("Location", f"{profile_data.get('city', '')}, {profile_data.get('country', '')}"),
        ("Primary Phone", profile_data.get('primary_phone', '')),
        ("Secondary Phone", profile_data.get('secondary_phone', '')),
        ("Profession", profile_data.get('profession', '')),
        ("Expertise", profile_data.get('expertise', '')),
        ("How I Can Help", profile_data.get('how_to_help', '')),
        ("Help Needed", profile_data.get('help_needed', '')),
        ("Business URL", profile_data.get('business_url', ''))
    ]
    
    for label, value in fields:
        if value:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, y, f"{label}:")
            text = p.beginText(150, y)
            text.setFont("Helvetica", 12)
            text.textLine(str(value))
            p.drawText(text)
            y -= line_spacing
    
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

# Profile View Handler
query_params = st.query_params
if 'profile_id' in query_params:
    profile = get_profile_by_id(query_params['profile_id'][0])
    if profile:
        st.title(f"Profile: {profile['full_name']}")
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                qr_img = generate_qr_code(query_params['profile_id'][0])
                if qr_img:
                    st.image(qr_img, width=200)
            with col2:
                st.markdown(f"**Profession:** {profile['profession']}")
                st.markdown(f"**Location:** {profile['city']}, {profile['country']}")
                st.markdown(f"**Expertise:** {profile['expertise']}")
                
        with st.expander("Contact Details"):
            st.write(f"**Email:** {profile['email']}")
            st.write(f"**Primary Phone:** {profile['primary_phone']}")
            if profile['secondary_phone']:
                st.write(f"**Secondary Phone:** {profile['secondary_phone']}")
                
        with st.expander("How I Can Help"):
            st.write(profile['how_to_help'])
            
        with st.expander("Help Needed"):
            st.write(profile['help_needed'] or "Not specified")
        
        st.stop()

# Main App
st.title("🌍 Karwan-e-Tijarat")

mode = st.radio("Profile Mode", ["Create New", "Update Existing"], horizontal=True)
profile_data = {}

if mode == "Update Existing":
    email_to_update = st.text_input("Enter your registered email")
    if st.button("Load Profile"):
        if email_to_update:
            profile_data = get_profile_by_email(email_to_update)
            if not profile_data:
                profile_data = {}  # 🛠 Ensure it's a dict to avoid AttributeError
                st.error("No profile found with this email")
            else:
                st.success("Profile loaded!")

form = st.form(key='profile_form')
with form:
    country_list = sorted([c.name for c in pycountry.countries if hasattr(c, 'name')])
    default_country = profile_data.get('country', 'Pakistan')
    
    col1, col2 = form.columns(2)
    with col1:
        country = form.selectbox("Country*", country_list, index=country_list.index(default_country) if default_country in country_list else 0)
    with col2:
        geolocator = Nominatim(user_agent="karwan_tijarat")
        try:
            location = geolocator.geocode(country)
            if location:
                city = form.text_input("City*", value=profile_data.get('city', ''))
            else:
                city = form.text_input("City*", value=profile_data.get('city', ''))
        except:
            city = form.text_input("City*", value=profile_data.get('city', ''))

    phone_code = get_country_phone_code(country)
    col1, col2 = form.columns(2)
    with col1:
        primary_phone = form.text_input(f"Primary Phone* ({phone_code})", value=profile_data.get('primary_phone', '').replace(phone_code, ''), placeholder="XXXXXXXXXX")
    with col2:
        secondary_phone = form.text_input("Secondary Phone", value=profile_data.get('secondary_phone', ''), placeholder="Optional")

    full_name = form.text_input("Full Name*", value=profile_data.get('full_name', ''))
    email = form.text_input("Email*", value=profile_data.get('email', ''))
    profession = form.text_input("Profession*", value=profile_data.get('profession', ''))
    expertise = form.text_area("Expertise*", value=profile_data.get('expertise', ''))
    how_to_help = form.text_area("How I Can Help*", value=profile_data.get('how_to_help', ''))
    help_needed = form.text_area("What Help Do I Need?", value=profile_data.get('help_needed', ''))
    business_url = form.text_input("Business URL", value=profile_data.get('business_url', ''), placeholder="https://example.com")
    
    submitted = form.form_submit_button("Save Profile")

if submitted:
    errors = []
    if not all([full_name, email, primary_phone, profession, expertise, how_to_help]):
        errors.append("Missing required fields (marked with *)")
    elif not validate_email(email):
        errors.append("Invalid email format")
    elif mode == "Create New" and get_profile_by_email(email):
        errors.append("Email already exists (use Update mode)")
    
    if errors:
        for error in errors: st.error(error)
    else:
        profile_data = {
            'id': profile_data.get('id', str(uuid.uuid4())),
            'full_name': full_name,
            'email': email,
            'city': city,
            'country': country,
            'primary_phone': format_phone(f"{phone_code}{primary_phone}", country),
            'secondary_phone': format_phone(secondary_phone, country) if secondary_phone else '',
            'profession': profession,
            'expertise': expertise,
            'how_to_help': how_to_help,
            'help_needed': help_needed,
            'business_url': business_url
        }

        if save_profile(profile_data):
            st.success("Profile saved successfully!")
            base_url = "https://karwan.streamlit.app"  # Adjust if deploying elsewhere
            profile_url = f"{base_url}?profile_id={profile_data['id']}"

            col1, col2 = st.columns(2)
            with col1:
                qr_img = generate_qr_code(profile_url)
                if qr_img:
                    st.image(qr_img, caption="Share Profile QR", width=200)
            with col2:
                st.markdown("**Shareable Profile URL:**")
                st.code(profile_url)

            pdf_bytes = generate_pdf(profile_data, qr_img)
            st.download_button("📄 Download Profile PDF", data=pdf_bytes, file_name=f"{full_name}_profile.pdf", mime="application/pdf")

            st.session_state.clear()
            st.experimental_rerun()

# Admin Section
if st.secrets.get("ADMIN_PASSWORD"):
    with st.expander("🔒 Admin Tools"):
        admin_pass = st.text_input("Enter Admin Password", type="password")
        if admin_pass == st.secrets["ADMIN_PASSWORD"]:
            if st.button("Export Full Database to CSV"):
                df = get_all_profiles()
                if not df.empty:
                    csv = df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    st.markdown(f'<a href="data:file/csv;base64,{b64}" download="karwan_profiles.csv">📥 Download CSV</a>', unsafe_allow_html=True)
                else:
                    st.warning("Database is empty")

# Search Section
st.divider()
st.subheader("🔍 Search Professionals")
search_term = st.text_input("Search by name, profession, expertise, or location")
if st.button("Search"):
    results = search_profiles(search_term)
    if not results.empty:
        st.write(f"Found {len(results)} profiles:")
        columns = st.columns(3)
        for idx, (_, row) in enumerate(results.iterrows()):
            with columns[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"### {row['full_name']}")
                    st.caption(f"**{row['profession']}**")
                    st.write(f"📍 {row['city']}, {row['country']}")
                    with st.expander("Details"):
                        st.write(f"**Expertise:** {row['expertise']}")
                        st.write(f"**Contact:** {row['email']}")
                        if row['business_url']:
                            st.markdown(f"[Website]({row['business_url']})")
                    if st.button("Download PDF", key=f"pdf_{row['id']}"):
                        pdf_bytes = generate_pdf(row.to_dict(), generate_qr_code(f"https://karwan.streamlit.app?profile_id={row['id']}"))
                        st.download_button(
                            label="Download",
                            data=pdf_bytes,
                            file_name=f"{row['full_name']}_profile.pdf",
                            mime="application/pdf",
                            key=f"dl_{row['id']}"
                        )
    else:
        st.warning("No matching profiles found")
