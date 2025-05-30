import imaplib
import email

def fetch_emails(config, since_date):
    # Connect to IMAP server
    mail = imaplib.IMAP4_SSL(config['host'], config['port'])
    mail.login(config['username'], config['password'])
    mail.select(config['folder'])
    # Search for emails
    if since_date is not None:
        since_str = since_date.strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{since_str}")')
    else:
        status, messages = mail.search(None, 'ALL')
    email_uids = messages[0].split()
    for uid in email_uids:
        status, msg_data = mail.fetch(uid, '(RFC822)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                yield uid.decode(), msg
    mail.logout()