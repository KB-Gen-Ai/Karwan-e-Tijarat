from fpdf import FPDF

def generate_pdf(profile_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Karwan-e-Tijarat Profile", ln=1, align='C')
    pdf.ln(10)
    
    fields = [
        ("Name", profile_data['full_name']),
        ("Email", profile_data['email']),
        ("Phone", profile_data['phone']),
        ("Profession", profile_data['profession']),
        ("Expertise", profile_data['expertise']),
        ("How I Can Help", profile_data['how_to_help'])
    ]
    
    for label, value in fields:
        pdf.cell(200, 10, txt=f"{label}: {value}", ln=1)
    
    return pdf.output(dest='S').encode('latin1')
