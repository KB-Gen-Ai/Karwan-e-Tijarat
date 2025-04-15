def generate_pdf(profile):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Karwan-e-Tijarat Member Profile", ln=True, align="C")
    pdf.ln(10)
    labels = ["Name", "Email", "Phone", "City", "Profession", "Skills", "Can Help With", "Needs Help With"]
    for label, val in zip(labels, profile[1:-1]):
        pdf.cell(200, 10, txt=f"{label}: {val}", ln=True)
    # QR Code
    profile_url = f"https://karwan.app/profile?email={profile[2]}&phone={profile[3]}"
    qr_bytes = generate_qr_code(profile_url)
    with open("temp_qr.png", "wb") as f:
        f.write(qr_bytes)
    pdf.image("temp_qr.png", x=160, y=10, w=40)
    
    # FIXED: Generate PDF in memory
    pdf_output = pdf.output(dest='S').encode('latin1')
    return pdf_output
