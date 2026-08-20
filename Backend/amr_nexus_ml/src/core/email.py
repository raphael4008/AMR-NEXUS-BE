import io
import smtplib
from datetime import datetime
from email.message import EmailMessage
from reportlab.pdfgen import canvas
from src.core.config import settings
from src.utils.logger import logger


def generate_and_send_pdf(email: str) -> None:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 800, "AMR Nexus Weekly Report")
    c.drawString(100, 780, f"Generated on {datetime.now().strftime('%Y-%m-%d')}")
    c.save()
    buffer.seek(0)

    msg = EmailMessage()
    msg["Subject"] = "AMR Nexus Weekly Report"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = email
    msg.set_content("Please find attached your AMR report.")
    msg.add_attachment(
        buffer.read(),
        maintype="application",
        subtype="pdf",
        filename="report.pdf",
    )

    with smtplib.SMTP(settings.SMTP_HOST, int(settings.SMTP_PORT)) as s:
        s.starttls()
        if settings.SMTP_USER and settings.SMTP_PASS:
            s.login(settings.SMTP_USER, settings.SMTP_PASS)
        s.send_message(msg)
    logger.info(f"Report emailed to {email}")
