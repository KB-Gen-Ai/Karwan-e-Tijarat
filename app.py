import streamlit as st
import sqlite3
from fpdf import FPDF
from database import init_db, DB_PATH
from auth import check_login, auth_section

# Initialize database and auth
init_db()
check_login()

def generate_pdf(member_data):
    """Generate PDF document from member data"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add content
    pdf.cell(200, 10, txt="Karwan-e-Tijarat Profile", ln=1, align='C')
    pdf.ln(10)
    
    # Profile fields
    fields = [
        ("Name", member_data['full_name']),
        ("Profession", member_data['profession']),
        ("Expertise", member_data['expertise']),
        ("Location", member_data['location']),
        ("Experience", f"{member_data['experience']} years"),
        ("Bio", member_data['bio'])
    ]
    
    for label, value in fields:
        pdf.cell(200, 10, txt=f"{label}: {value}", ln=1)

    # Convert PDF to bytes for download
    return bytes(pdf.output(dest='S').encode('latin1'))

def profile_section():
    """Display and edit user profile"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    user_email = st.session_state.get("user_email")
    if not user_email:
        st.error("User session not found. Please log in again.")
        st.stop()

    c.execute("SELECT * FROM members WHERE email=?", (user_email,))
    data = c.fetchone()
    
    if data:
        st.header("My Profile")
        
        # Profile form
        with st.form("profile_form"):
            name = st.text_input("Full Name", value=data[1])
            profession = st.text_input("Profession", value=data[2])
            expertise = st.text_input("Expertise", value=data[3])
            location = st.text_input("Location", value=data[6])
            experience = st.number_input("Experience (years)", value=data[7])
            bio = st.text_area("Bio", value=data[10], height=150)
            
            # Form actions
            col1, col2 = st.columns(2)
            with col1:
                update_btn = st.form_submit_button("Update Profile")
            
            if update_btn:
                c.execute("""UPDATE members SET
                    full_name=?, profession=?, expertise=?,
                    location=?, experience=?, bio=?
                    WHERE email=?""",
                    (name, profession, expertise, location,
                     experience, bio, user_email))
                conn.commit()
                st.success("Profile updated!")
            
            with col2:
                if st.form_submit_button("Generate PDF"):
                    pdf_data = generate_pdf({
                        'full_name': name,
                        'profession': profession,
                        'expertise': expertise,
                        'location': location,
                        'experience': experience,
                        'bio': bio
                    })
                    st.download_button(
                        label="Download PDF",
                        data=pdf_data,
                        file_name=f"{name}_profile.pdf",
                        mime="application/pdf"
                    )
    
    conn.close()

def search_members():
    """Search professionals"""
    st.header("Find Professionals")
    search = st.text_input("Search by name, profession or location")
    
    if st.button("Search"):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""SELECT full_name, profession, expertise, location, email 
                     FROM members 
                     WHERE full_name LIKE ? OR profession LIKE ? OR location LIKE ?""",
                  (f"%{search}%", f"%{search}%", f"%{search}%"))
        results = c.fetchall()
        
        if results:
            for name, prof, exp, loc, email in results:
                st.markdown(f"**{name}** - *{prof}*")
                st.markdown(f"📍 {loc} | 🛠️ {exp}")
                with st.expander("Contact"):
                    st.markdown(f"📧 {email}")
        else:
            st.warning("No matching professionals found")
        conn.close()

# Main app flow
if not st.session_state.get("logged_in"):
    auth_section()
    st.stop()

st.sidebar.title("Menu")
page = st.sidebar.radio("Navigation", ["My Profile", "Search Members"])

if page == "My Profile":
    profile_section()
else:
    search_members()
