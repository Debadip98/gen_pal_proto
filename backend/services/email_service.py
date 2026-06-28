"""Email service for GenPal SME review notifications.

Gracefully degrades to a no-op when email is not configured.
Supports SMTP and SendGrid providers.
"""

from __future__ import annotations

from backend.core import config


def send_review_link(
    sme_email: str,
    review_link: str,
    skill_name: str,
    requestor_email: str,
) -> bool:
    """Send SME review link. Returns True if sent, False if email not configured."""
    if not config.is_email_configured():
        return False

    subject = f"GenPal Question Bank Review Request — {skill_name}"
    body = _build_review_email_body(review_link, skill_name, requestor_email)

    provider = config.get_email_provider()
    if provider == "smtp":
        return _send_smtp(sme_email, subject, body)
    if provider == "sendgrid":
        return _send_sendgrid(sme_email, subject, body)
    return False


def _build_review_email_body(review_link: str, skill_name: str, requestor_email: str) -> str:
    return (
        f"Hello,\n\n"
        f"You have been requested to review a GenPal question bank for skill: {skill_name}.\n\n"
        f"Please click the link below to access the review:\n{review_link}\n\n"
        f"This link will expire in {config.get_review_token_expiry_hours()} hours.\n\n"
        f"Requested by: {requestor_email}\n\n"
        "Thank you,\nGenPal Question Bank Factory"
    )


def _send_smtp(to_email: str, subject: str, body: str) -> bool:
    import smtplib
    from email.mime.text import MIMEText

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = config.get_email_from() or config.get_smtp_username() or "noreply@genpal"
        msg["To"] = to_email

        with smtplib.SMTP(config.get_smtp_host(), config.get_smtp_port()) as server:
            server.starttls()
            username = config.get_smtp_username()
            password = config.get_smtp_password()
            if username and password:
                server.login(username, password)
            server.send_message(msg)
        return True
    except Exception:
        return False


def _send_sendgrid(to_email: str, subject: str, body: str) -> bool:
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail

        sg = sendgrid.SendGridAPIClient(api_key=config.get_sendgrid_api_key())
        message = Mail(
            from_email=config.get_sendgrid_from_email() or "noreply@genpal.example.com",
            to_emails=to_email,
            subject=subject,
            plain_text_content=body,
        )
        response = sg.send(message)
        return response.status_code in (200, 201, 202)
    except Exception:
        return False
