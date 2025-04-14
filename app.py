import streamlit as st
import pandas as pd
import uuid
from database import save_profile, get_profile_by_id, init_db, DB_PATH
from auth import check_login, auth_section
from pdf_generator import generate_pdf
from qr_generator import generate_qr_code

# Initialize database and auth
init_db()
check_login()

# Set page config
st.set_page_config(page_title="Karwan-e-Tijarat", layout="centered")

# 🌍 Display banner
st.markdown("<h1 style='text-align: center;'>🌍 Karwan-e-Tijarat</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Connecting professionals for collaboration and national brand-building.</p>", unsafe_allow_html=True)
st.markdown("---")

# --- Handle shared profile link ---
query_params = st.query_params
if "profile_id" in query_params:
    profile_id = query_params["profile_id"][0]
    profile_data = get_profile_by_id(profile_id)

    if profile_data:
        st.subheader("📄 Public Profile View (Read-Only)")

        st.write(f"**Name:** {profile_data['full_name']}")
        st.write(f"**Email:** {profile_data['email']}")
        st.write(f"**Phone:** {profile_data['phone']}")
        st.write(f"**Profession:** {profile_data['profession']}")
        st.write(f"**Expertise:** {profile_data['expertise']}")
        st.write(f"**How I Can Help:** {profile_data['how_to_help']}")

        if st.button("📄 Download Profile as PDF"):
            pdf_bytes = generate_pdf(profile_data)
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=f"{profile_data['full_name']}_profile.pdf",
                mime="application/pdf"
            )

        st.stop()
    else:
        st.error("❌ Profile not found.")
        st.stop()

# --- Main profile form ---
if not st.session_state.logged_in:
    auth_section()
    st.stop()

st.subheader("📝 Register Your Profile")

with st.form("profile_form"):
    full_name = st.text_input("👤 Full Name")
    email = st.text_input("📧 Email")
    phone = st.text_input("📱 Phone Number")
    profession = st.text_input("💼 Profession / Job Title")
    expertise = st.text_area("📚 Areas of Expertise")
    how_to_help = st.text_area("🤝 How Can You Help Other Members?")

    submitted = st.form_submit_button("✅ Submit My Profile")

if submitted:
    profile_id = str(uuid.uuid4())

    profile_data = {
        "id": profile_id,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "profession": profession,
        "expertise": expertise,
        "how_to_help": how_to_help,
    }

    save_profile(profile_data)

    profile_url = f"https://karwan-e-tijarat.streamlit.app/?profile_id={profile_id}"
    qr_image = generate_qr_code(profile_url)

    st.success("🎉 Your profile has been saved!")

    st.markdown(f"🔗 **Share your profile:** [Click here to view]({profile_url})")
    st.image(qr_image, caption="📱 Scan to view your profile", use_column_width=False)

    st.download_button(
        label="📄 Download Profile as PDF",
        data=generate_pdf(profile_data),
        file_name=f"{full_name}_profile.pdf",
        mime="application/pdf"
    )

# Search functionality
st.markdown("---")
st.subheader("🔍 Search Members")

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
            st.markdown(f"### {name}")
            st.markdown(f"**Profession:** {prof}")
            st.markdown(f"**Expertise:** {exp}")
            with st.expander("Contact Info"):
                st.markdown(f"📧 {email}")
                st.markdown(f"📱 {phone}")
    else:
        st.warning("No matching members found")
    conn.close()
