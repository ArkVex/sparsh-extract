import requests
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Create a simple test PDF with more than 111 pages
def create_test_pdf():
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Create 120 pages to test our 51-111 range
    for page_num in range(1, 121):
        p.drawString(100, 750, f"Test Page {page_num}")
        p.drawString(100, 700, "This is a test PDF for clinical study protocol extraction")
        p.drawString(100, 650, f"Page {page_num} of 120")
        p.showPage()
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

# Test the extract endpoint
url = "http://127.0.0.1:5000/extract"

try:
    # Create a proper test PDF
    pdf_content = create_test_pdf()
    files = {'file': ('test_clinical_study.pdf', io.BytesIO(pdf_content), 'application/pdf')}
    
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Extract endpoint is working")
        print("Response keys:", list(response.json().keys()))
    else:
        print(f"Error Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")