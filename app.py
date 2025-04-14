import streamlit as st
import sqlite3
import re
import qrcode  # For generating QR codes
from fpdf import FPDF
from database import init_db, DB_PATH
from auth import check_login, auth_section
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

# Initialize database and auth
init_db()
check_login()

# Function to generate the PDF
def generate_pdf(member_data, img_path=None):
    """Generate PDF document from member data, including profile picture and QR code."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add title
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
    
    # Add profile fields
    for label, value in fields:
        pdf.cell(200, 10, txt=f"{label}: {value}", ln=1)

    # Add profile picture if available
    if img_path:
        pdf.ln(10)
        pdf.cell(200, 10, txt="Profile Picture", ln=1)
        pdf.image(img_path, x=10, y=pdf.get_y(), w=30)  # Adjust position/size if needed

    # Add QR code with email
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f"mailto:{member_data['email']}")
    qr.make(fit=True)

    qr_img = qr.make_image(fill="black", back_color="white")
    qr_img_path = "qr_code.png"
    qr_img.save(qr_img_path)

    # Add QR code to PDF
    pdf.ln(10)
    pdf.cell(200, 10, txt="QR Code (Scan to Email)", ln=1)
    pdf.image(qr_img_path, x=10, y=pdf.get_y(), w=30)  # Adjust position/size if needed

    # Output PDF
    output = pdf.output(dest='S')
    if isinstance(output, str):
        output = output.encode('latin1')
    return output if output else None

# Function to send email with the PDF
def send_email(pdf_data, user_email):
    """Send the PDF via email."""
    from_email = "your_email@example.com"  # Replace with your email
    to_email = user_email

    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Your Karwan-e-Tijarat Profile PDF"

    # Attach the PDF to the email
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_data)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename=profile.pdf")
    msg.attach(part)

    # Send email
    try:
        with smtplib.SMTP('smtp.example.com', 587) as server:  # Replace with your SMTP server
            server.starttls()
            server.login(from_email, "your_password")  # Replace with your email login credentials
            server.sendmail(from_email, to_email, msg.as_string())
        st.success("PDF sent to your email!")
    except Exception as e:
        st.error(f"Error sending email: {e}")

# Profile section for users to update their profiles
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
            profile_pic = st.file_uploader("Upload Profile Picture", type=["jpg", "jpeg", "png"])

            col1, col2 = st.columns(2)

            with col1:
                update_btn = st.form_submit_button("Update Profile")

            if update_btn:
                # If profile picture is uploaded, save it
                img_path = None
                if profile_pic:
                    img_path = f"images/{user_email}_profile_pic.jpg"
                    with open(img_path, "wb") as f:
                        f.write(profile_pic.getbuffer())

                # Update profile in the database
                c.execute("""UPDATE members SET
                    full_name=?, profession=?, expertise=?,
                    location=?, experience=?, bio=?,
                    profile_pic=? WHERE email=?""",
                    (name, profession, expertise, location,
                     experience, bio, img_path, user_email))
                conn.commit()
                st.success("Profile updated!")

            with col2:
                if st.form_submit_button("Generate PDF"):
                    # Generate PDF
                    pdf_data = generate_pdf({
                        'full_name': name,
                        'profession': profession,
                        'expertise': expertise,
                        'location': location,
                        'experience': experience,
                        'bio': bio,
                        'email': user_email
                    }, img_path)

                    if pdf_data:
                        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
                        st.download_button(
                            label="Download PDF",
                            data=pdf_data,
                            file_name=f"{safe_name}_profile.pdf",
                            mime="application/pdf"
                        )

                        # Option to email the PDF
                        if st.button("Email PDF"):
                            send_email(pdf_data, user_email)
                    else:
                        st.warning("PDF generation failed. Please try again.")

    conn.close()

# Member search section
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
