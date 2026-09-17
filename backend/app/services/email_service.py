import logging
from typing import Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def format_case_email(
        self,
        case_number: str,
        case_title: str,
        event_title: str,
        event_message: str,
        recipient_name: str,
        action_url: Optional[str] = None,
    ) -> Tuple[str, str, str]:
        """
        Generates subject, plain text body, and clean responsive HTML template for municipal case events.
        """
        subject = f"[AI Municipal Grievance] {event_title}: {case_number}"

        text_body = f"""Hello {recipient_name},

{event_title}
Case: {case_number} - {case_title}

{event_message}

You can view the full timeline, details, and updates in the AI Case Manager application.

Best regards,
Municipal Grievance Redressal Team
"""

        html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }}
    .header {{ background: #0284c7; padding: 24px; color: #ffffff; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; }}
    .content {{ padding: 24px; line-height: 1.6; font-size: 14px; }}
    .badge {{ display: inline-block; padding: 4px 10px; background: #e0f2fe; color: #0369a1; border-radius: 20px; font-weight: 600; font-size: 12px; }}
    .card {{ background: #f1f5f9; padding: 16px; border-radius: 8px; margin: 16px 0; border-left: 4px solid #0284c7; }}
    .footer {{ background: #f8fafc; padding: 16px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>AI Municipal Grievance Redressal</h1>
    </div>
    <div class="content">
      <p>Hello <strong>{recipient_name}</strong>,</p>
      <div class="badge">{event_title}</div>
      <div class="card">
        <strong>Case {case_number}</strong>: {case_title}<br>
        <p style="margin: 8px 0 0 0; color: #334155;">{event_message}</p>
      </div>
      <p>To view real-time updates or respond, please check the AI Case Manager portal.</p>
    </div>
    <div class="footer">
      This is an automated transactional notification from Municipal Corporation. Please do not reply directly.
    </div>
  </div>
</body>
</html>
"""
        return subject, text_body, html_body

    def send_transactional_email(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: Optional[str] = None,
        event_type: str = "general",
    ) -> bool:
        """
        Dispatches transactional email. Never raises runtime exceptions so core case transitions
        are never blocked by external network or email provider downtime.
        """
        try:
            # In development/test and free-tier environments without external SMTP, log delivery
            logger.info(
                f"[TRANSACTIONAL EMAIL DISPATCH] To: {to_email} | Subject: {subject} | Event: {event_type}\n"
                f"Body: {text_body.strip()[:160]}..."
            )
            return True
        except Exception as e:
            logger.error(f"Failed to dispatch email to {to_email}: {e}")
            return False


email_service = EmailService()
