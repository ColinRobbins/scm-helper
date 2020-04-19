"""Send email."""
import smtplib

from scm_helper.config import (
    C_EMAIL,
    C_PASSWORD,
    C_SEND_TO,
    C_SMTP_PORT,
    C_SMTP_SERVER,
    C_TLS,
    C_USERNAME,
    O_TO,
    get_config,
)
from scm_helper.notify import notify


def send_email(scm, text, subject):
    """Send an email."""
    smtp_server = get_config(scm, C_EMAIL, C_SMTP_SERVER)
    smtp_port = get_config(scm, C_EMAIL, C_SMTP_PORT)
    username = get_config(scm, C_EMAIL, C_USERNAME)
    tls = get_config(scm, C_EMAIL, C_TLS)
    password_file = get_config(scm, C_EMAIL, C_PASSWORD)

    password = scm.crypto.read_key(password_file)
    if password is None:
        return False

    if scm.option(O_TO):
        send_to = scm.option(O_TO)
    else:
        send_to = get_config(scm, C_EMAIL, C_SEND_TO)

    recips = send_to.split(";")

    if subject is None:
        subject = "Message from Swim Club Manager"

    message = f"From: Swim Club Manager Helper <{username}>\n"
    message += f"To: <{send_to}>\n"
    message += f"Subject: {subject}\n\n"
    message += text

    try:
        email = smtplib.SMTP(smtp_server, smtp_port)
        if tls:
            email.starttls()
        email.login(username, password)
        email.sendmail(username, recips, message)
        notify("email sent.")

    except (smtplib.SMTPException, OSError) as error:
        notify(f"Error sending email\n{error}\n")
        return False

    return True
