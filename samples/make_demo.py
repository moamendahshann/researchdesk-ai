"""Generate a fictional three-page test document. Requires requirements-dev.txt."""
from pathlib import Path
from reportlab.pdfgen import canvas
p = Path(__file__).with_name('demo.pdf')
c = canvas.Canvas(str(p))
sections = [
 ('Community Energy', 'Solar panels supply electricity to the fictional community centre.'),
 ('Inclusive Transport', 'Bicycle repair workshops teach volunteers how to maintain bicycles.'),
 ('Food Solidarity', 'Food collection sessions support a fictional neighbourhood pantry.')]
for title, body in sections:
    c.setFont('Helvetica-Bold',20); c.drawString(50,780,title)
    c.setFont('Helvetica',11); c.drawString(50,740,body)
    c.drawString(50,700,'Fictional demonstration content. Not a record of real projects.')
    c.showPage()
c.save()
print(p)
