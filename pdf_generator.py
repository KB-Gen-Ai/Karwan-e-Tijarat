from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

def generate_pdf(profile_data):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Set font
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "Karwan-e-Tijarat Profile")
    
    # Profile data
    p.setFont("Helvetica", 12)
    y_position = 700
    for field, value in [
        ("Name", profile_data['full_name']),
        ("Email", profile_data['email']),
        ("Phone", profile_data['phone']),
        ("Profession", profile_data['profession']),
        ("Expertise", profile_data['expertise']),
        ("How I Can Help", profile_data['how_to_help'])
    ]:
        p.drawString(100, y_position, f"{field}: {value}")
        y_position -= 30
    
    p.save()
    buffer.seek(0)
    return buffer.read()
