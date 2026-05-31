import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import structlog
from app.config import settings

logger = structlog.get_logger()

class EmailService:
    @staticmethod
    async def send_password_reset_email(email_to: str, token: str) -> bool:
        """
        Sends a password reset link to the specified email address.
        If no SMTP configuration is available, logs the details in development mode.
        """
        reset_link = f"http://localhost/reset-password?token={token}"
        
        subject = "Recuperación de Contraseña - CRM Estudio de Abogados"
        body_text = f"""
Hola,

Has solicitado restablecer tu contraseña en el sistema CRM del Estudio de Abogados.
Por favor, haz clic en el siguiente enlace para establecer una nueva contraseña (este enlace expira en 15 minutos):

{reset_link}

Si no has realizado esta solicitud, puedes ignorar este correo de forma segura.

Saludos cordiales,
El equipo de Soporte.
"""
        
        # Check if SMTP configuration is provided
        if not settings.SMTP_HOST:
            # Fallback to logging for development/MVP testing
            logger.warn(
                "DEVELOPMENT EMAIL ALERT: No SMTP server configured. Printing reset link here.",
                recipient=email_to,
                reset_link=reset_link,
                token=token
            )
            return True

        try:
            # Construct Email message
            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_FROM
            msg["To"] = email_to
            msg["Subject"] = subject
            msg.attach(MIMEText(body_text, "plain"))

            # Connect to SMTP server
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            # Send Email
            server.sendmail(settings.SMTP_FROM, email_to, msg.as_string())
            server.quit()
            
            logger.info("Password reset email sent successfully", recipient=email_to)
            return True
            
        except Exception as e:
            logger.error("Failed to send password reset email", recipient=email_to, error=str(e))
            return False
