from email.message import EmailMessage
import smtplib
import ssl


def send_email_report(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    recipient: str,
    subject: str,
    body: str,
) -> None:
    if not username.strip() or not password.strip():
        raise ValueError(
            "Set MARKET_SMTP_USERNAME and MARKET_SMTP_PASSWORD to enable market "
            "summary email delivery. Use a provider app password, not your account password."
        )
    if not recipient.strip():
        raise ValueError("MARKET_REPORT_EMAIL must be a non-empty email address.")

    message = EmailMessage()
    message["From"] = username
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ssl.create_default_context())
        smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(message)
