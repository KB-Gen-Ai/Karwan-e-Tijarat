import streamlit as st
import sqlite3
from database import init_db, DB_PATH
from auth import check_login, auth_section

# Initialize database and auth
init_db()
check_login()

def profile_section():
    """Display and edit user profile"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM members WHERE email=?", (st.session_state.user_email,))
    data = c.fetchone()
    
    if data:
        st.header("My Profile")
        
        with st.form("profile_form"):
            name = st.text_input("Full Name", value=data[1])
            profession = st.text_input("Profession", value=data[2])
            expertise = st.text_input("Expertise", value=data[3])
            location = st.text_input("Location", value=data[6])
            experience = st.number_input("Experience (years)", value=data[7])
            bio = st.text_area("Bio", value=data[10], height=150)
            
            if st.form_submit_button("Update Profile"):
                c.execute("""UPDATE members SET
                    full_name=?, profession=?, expertise=?,
                    location=?, experience=?, bio=?
                    WHERE email=?""",
                    (name, profession, expertise, location,
                     experience, bio, st.session_state.user_email))
                conn.commit()
                st.success("Profile updated!")
    
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
if not st.session_state.logged_in:
    auth_section()
    st.stop()

st.sidebar.title("Menu")
page = st.sidebar.radio("Navigation", ["My Profile", "Search Members"])

if page == "My Profile":
    profile_section()
else:
    search_members()
