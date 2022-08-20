import smtplib
from email import encoders
import gnupg
import os
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.message import Message
from email.mime.multipart import MIMEMultipart


def log_in(email_address,password):
    server = smtplib.SMTP("smtp.gmail.com",587)

    server.ehlo()
    server.starttls()

    server.login(email_address, password)
    return server

def send_email(email_address,server,recipient_email,subject,email_content):

    current_path = os.path.join(os.getcwd(),"PGP FILE")
    gpg = gnupg.GPG(gnupghome=current_path)
    Public_Key = gpg.export_keys(email_address)

    message = Message()
    message.add_header(_name="Content-Type", _value="multipart/mixed", protected_headers="v1")
    message["From"] = email_address
    message["To"] = recipient_email
    message["Subject"] = subject

    message_text = Message()
    message_text.add_header(_name="Content-Type", _value="multipart/mixed")
    message_text.add_header(_name="Content-Language", _value="en-US")
    message_body = Message()
    message_body.add_header(_name="Content-Type", _value="text/plain", charset="utf-8")
    message_body.add_header(_name="Content-Transfer-Encoding", _value="quoted-printable")
    message_body.set_payload(email_content + 2*"\n")

    message_text.attach(message_body)
    message.attach(message_text)

    encrypted_message = MIMEBase(_maintype="multipart", _subtype="encrypted", protocol="application/pgp-encrypted")
    encrypted_message["From"] = email_address
    encrypted_message["To"] = recipient_email
    encrypted_message["Subject"] = subject

    encrypted_message1 = Message()
    encrypted_message1.add_header(_name="Content-Type", _value="application/pgp-encrypted")
    encrypted_message1.add_header(_name="Content-Description", _value="PGP/MIME version identification")
    encrypted_message1.set_payload("Version: 1" + "\n")

    encrypted_message2 = Message()
    encrypted_message2.add_header(_name="Content-Type", _value="application/octet-stream")
    encrypted_message2.add_header(_name="Content-Description", _value="OpenPGP encrypted message")
    encrypted_message2.add_header(_name="Content-Disposition", _value="inline")
    encrypted_message2.set_payload(str(gpg.encrypt(message.as_string(), recipient_email,sign=Public_Key)))

    encrypted_message.attach(encrypted_message1)
    encrypted_message.attach(encrypted_message2)

    server.sendmail(email_address, recipient_email, encrypted_message.as_string())
