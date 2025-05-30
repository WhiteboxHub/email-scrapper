import yaml
from extractor import email_client, filter, parser, db, logger
from datetime import datetime

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    import sys
    config = load_config('config.yaml')
    db.init_db()
    account_email = config['email']['username']
    last_run = db.get_last_run_date_for_account(account_email)
    count = 0
    extracted_by = config['email']['username']
    extraction_run_end = datetime.now().isoformat()

    for uid, msg in email_client.fetch_emails(config['email'], last_run):
        if filter.is_relevant(msg, config['rules']):
            print(f"[EXTRACTING] Email UID {uid}: {msg.get('From', '')}", file=sys.stderr)
            contact = parser.extract_contact(uid, msg)
            if not db.exists(contact.email):
                db.insert(contact)
                logger.log_csv(contact, extracted_by, extraction_run_end)
                count += 1
            else:
                print(f"[SKIP] Contact with email {contact.email} already exists.", file=sys.stderr)
        else:
            print(f"[NOT EXTRACTING] Email UID {uid}: {msg.get('From', '')}", file=sys.stderr)
    db.update_last_run_date_for_account(account_email, extraction_run_end)
    logger.log_summary(extracted_by, extraction_run_end, count)
    logger.report_summary(count)

if __name__ == "__main__":
    main()