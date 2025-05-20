import os
import imaplib
import email
from dotenv import load_dotenv
from typing import List, Dict
import pandas as pd
from tqdm import tqdm  # optional for progress bar
from utils import EmailParser


class EmailScraper:
    def __init__(self):
        load_dotenv()  # Load environment variables from .env file
        
        self.email_address = os.getenv('EMAIL')
        self.email_password = os.getenv('PASSWORD')
        self.imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        self.output_dir = os.getenv('OUTPUT_DIR', 'output')
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.mail = None

    def connect(self) -> bool:
        """Connect to IMAP server"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email_address, self.email_password)
            self.mail.select('inbox')  # Select inbox folder
            return True
        except Exception as e:
            print(f"Connection failed: {str(e)}")
            return False

    def fetch_emails(self, limit: int = 100) -> List[Dict[str, str]]:
        """Fetch and process emails"""
        if not self.mail:
            if not self.connect():
                return []
        
        contacts = []
        try:
            # Search for all emails
            status, messages = self.mail.search(None, 'ALL')
            if status != 'OK':
                print("No messages found!")
                return []
            
            email_ids = messages[0].split()
            
            # Process emails (limited by 'limit' parameter)
            for email_id in tqdm(email_ids[:limit], desc="Processing emails"):
                try:
                    status, msg_data = self.mail.fetch(email_id, '(RFC822)')
                    if status != 'OK':
                        continue
                        
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    
                    contact_info = EmailParser.extract_contact_info(email_message)
                    if any(contact_info.values()):  # Only add if we have some data
                        contacts.append(contact_info)
                except Exception as e:
                    print(f"Error processing email {email_id}: {str(e)}")
                    continue
        
        except Exception as e:
            print(f"Error fetching emails: {str(e)}")
        
        return contacts

    def save_to_csv(self, contacts: List[Dict[str, str]], filename: str = 'extracted_contacts.csv') -> str:
        """Save contacts to CSV file"""
        if not contacts:
            print("No contacts to save")
            return ""
        
        output_path = os.path.join(self.output_dir, filename)
        
        # Convert to DataFrame for easier CSV handling
        df = pd.DataFrame(contacts)
        
        # Drop duplicates based on email (assuming same email = same contact)
        df.drop_duplicates(subset=['email'], inplace=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        print(f"Saved {len(df)} contacts to {output_path}")
        return output_path

    def run(self, limit: int = 100, output_filename: str = 'extracted_contacts.csv'):
        """Run the complete scraping process"""
        if not self.connect():
            return
        
        contacts = self.fetch_emails(limit)
        self.save_to_csv(contacts, output_filename)
        self.disconnect()

    def disconnect(self):
        """Close the IMAP connection"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
            except:
                pass
            finally:
                self.mail = None


if __name__ == "__main__":
    scraper = EmailScraper()
    scraper.run(limit=50)  # Process first 50 emails