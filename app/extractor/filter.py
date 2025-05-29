def is_relevant(msg, config):
    # Check sender domain
    sender = msg.get('From', '')
    if any(domain in sender for domain in config['sender_domains']):
        return True
    # Check subject keywords
    subject = msg.get('Subject', '').lower()
    if any(keyword in subject for keyword in config['subject_keywords']):
        return True
    # Check body keywords
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(errors='ignore').lower()
                if any(keyword in body for keyword in config['body_keywords']):
                    return True
    else:
        body = msg.get_payload(decode=True).decode(errors='ignore').lower()
        if any(keyword in body for keyword in config['body_keywords']):
            return True
    return False