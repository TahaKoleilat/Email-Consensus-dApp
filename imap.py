# Importing libraries
import imaplib
import email
import gnupg
import os


def read_email(email_address,password,subject,recipient_address):

    current_path = os.path.join(os.getcwd(),"PGP FILE")
    gpg = gnupg.GPG(gnupghome=current_path)

    imap_url = 'imap.gmail.com'

    imap_server = imaplib.IMAP4_SSL(imap_url)

    imap_server.login(email_address, password)

    imap_server.select('Inbox')

    _, data = imap_server.search(None, '(FROM "{}" SUBJECT "{}")'.format(recipient_address,subject))

    mail_id_list = data[0].split()

    msgs = []

    for num in mail_id_list:
        typ, data = imap_server.fetch(num, '(RFC822)')
        msgs.append(data)

    for msg in msgs[::-1]:
        for response_part in msg:
            if type(response_part) is tuple:
                my_msg=email.message_from_bytes((response_part[1]))
                email_message = ""
                email_message += "_________________________________________\n"
                email_message += "subj: " + my_msg['subject'] + '\n'
                email_message +="from:" + my_msg['from'] + '\n'
                email_message += "body: \n"
                for part in my_msg.walk():  
                    if part.get_content_type() == 'application/octet-stream':
                         email_message += str(gpg.decrypt(part.get_payload()))
                         return email_message