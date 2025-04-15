import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import qrcode
import io
import base64
from fpdf import FPDF
import re

# Database setup
conn = sqlite3.connect('karwan_e_tijarat.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        city TEXT,
        country TEXT,
        profession TEXT,
        skills TEXT,
        help_offer TEXT,
        help_seek TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Admin credentials (for demo purposes)
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "testpass")

# Helpers

def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validate_phone(phone):
    return re.match(r"^[0-9\-\+]{9,15}$", phone)

def get_profile_by_email_phone(email, phone):
    c.execute("SELECT * FROM profiles WHERE email = ? AND phone = ?", (email, phone))
    return c.fetchone()

def insert_or_update_profile(data):
    existing = get_profile_by_email_phone(data['email'], data['phone'])
    if existing:
        c.execute('''
            UPDATE profiles SET name=?, city=?, country=?, profession=?, skills=?, help_offer=?, help_seek=?, timestamp=CURRENT_TIMESTAMP
            WHERE email=? AND phone=?
        ''', (data['name'], data['city'], data['country'], data['profession'], data['skills'], data['help_offer'], data['help_seek'], data['email'], data['phone']))
    else:
        c.execute('''
            INSERT INTO profiles (name, email, phone, city, country, profession, skills, help_offer, help_seek)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['email'], data['phone'], data['city'], data['country'], data['profession'], data['skills'], data['help_offer'], data['help_seek']))
    conn.commit()

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def generate_pdf(profile):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Karwan-e-Tijarat Member Profile", ln=True, align="C")
    pdf.ln(10)
    labels = ["Name", "Email", "Phone", "City", "Country", "Profession", "Skills", "Can Help With", "Needs Help With"]
    for label, val in zip(labels, profile[1:-1]):
        pdf.cell(200, 10, txt=f"{label}: {val}", ln=True)
    profile_url = f"https://karwan.app/profile?email={profile[2]}&phone={profile[3]}"
    qr_bytes = generate_qr_code(profile_url)
    with open("temp_qr.png", "wb") as f:
        f.write(qr_bytes)
    pdf.image("temp_qr.png", x=160, y=10, w=40)
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()

def download_button(data, filename, label):
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{label}</a>'
    return href

# UI
st.set_page_config(page_title="Karwan-e-Tijarat Connect", layout="centered")
st.title("🤝 Karwan-e-Tijarat")
st.markdown("Helping professionals across the nation connect, collaborate, and grow.")

menu = st.sidebar.selectbox("Navigation", ["Submit/Update Profile", "Search Directory", "Admin: Export Data"])

if menu == "Submit/Update Profile":
    st.subheader("📝 Enter Your Profile")
    with st.form("profile_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        city = st.text_input("City")
        country = st.text_input("Country")
        profession = st.text_input("Profession")
        skills = st.text_area("Your Skills & Expertise")
        help_offer = st.text_area("How You Can Help Others")
        help_seek = st.text_area("What Help You Are Looking For")
        submitted = st.form_submit_button("Submit / Update")

        if submitted:
            if not (name and email and phone):
                st.error("Name, Email, and Phone are required.")
            elif not validate_email(email):
                st.error("Invalid email format.")
            elif not validate_phone(phone):
                st.error("Invalid phone number.")
            else:
                data = {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'city': city,
                    'country': country,
                    'profession': profession,
                    'skills': skills,
                    'help_offer': help_offer,
                    'help_seek': help_seek
                }
                insert_or_update_profile(data)
                st.success("Profile saved successfully!")
                profile_url = f"https://karwan.app/profile?email={email}&phone={phone}"
                st.markdown(f"🔗 **Your Shareable Profile Link:** [Click Here]({profile_url})")
                st.image(generate_qr_code(profile_url), caption="Scan this QR to share your profile")
                st.markdown(download_button(generate_pdf((0, name, email, phone, city, country, profession, skills, help_offer, help_seek)),
                                           f"Karwan_Profile_{name}.pdf", "📄 Download PDF"), unsafe_allow_html=True)

elif menu == "Search Directory":
    st.subheader("🔍 Search Profiles")
    search_term = st.text_input("Search by Name, City, Country, or Profession")
    if search_term:
        query = f"""
            SELECT * FROM profiles
            WHERE name LIKE ? OR city LIKE ? OR country LIKE ? OR profession LIKE ?
            ORDER BY timestamp DESC
        """
        c.execute(query, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        results = c.fetchall()
        if results:
            for r in results:
                st.markdown("---")
                st.markdown(f"**👤 Name:** {r[1]}")
                st.markdown(f"📍 **City:** {r[4]}")
                st.markdown(f"🌏 **Country:** {r[5]}")
                st.markdown(f"💼 **Profession:** {r[6]}")
                st.markdown(f"🛠️ **Skills:** {r[7]}")
                st.markdown(f"🤝 **Can Help With:** {r[8]}")
                st.markdown(f"🙏 **Needs Help With:** {r[9]}")
                profile_url = f"https://karwan.app/profile?email={r[2]}&phone={r[3]}"
                st.markdown(f"🔗 [View Profile Link]({profile_url})")
        else:
            st.warning("No profiles found matching your search.")

elif menu == "Admin: Export Data":
    st.subheader("📄 Export Directory (Admin Only)")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if admin_pass == ADMIN_PASSWORD:
        df = pd.read_sql_query("SELECT * FROM profiles", conn)
        st.dataframe(df)
        csv = df.to_csv(index=False).encode()
        st.download_button("Download CSV", csv, "karwan_profiles.csv", "text/csv")
    else:
        st.warning("Access denied. Only admin can export data.")
