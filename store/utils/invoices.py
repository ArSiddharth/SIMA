
# store/utils/invoices.py
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def generate_invoice_pdf(file_path: Path, invoice, delivery):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(file_path), pagesize=A4)
    c.setFont("Helvetica", 12)
    c.drawString(72, 800, f"Invoice #{invoice.pk} for Delivery #{delivery.pk}")
    c.drawString(72, 780, f"Customer: {invoice.customer_name}")
    c.drawString(72, 760, f"Item: {invoice.item}  Qty: {invoice.quantity}")
    c.drawString(72, 740, f"Price per item: {invoice.price_per_item}")
    c.drawString(72, 720, f"Shipping: {invoice.shipping}")
    c.showPage()
    c.save()
