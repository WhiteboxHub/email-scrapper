import mysql.connector
from mysql.connector import Error
from models.contact import Contact
import os
from datetime import datetime, timedelta

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("PORT"))

TABLE_NAME = "contacts_extractor"
SPECIAL_LAST_RUN_EMAIL = "__LAST_RUN__"

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )
def init_db():
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(f'''CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            email VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255),
            phone VARCHAR(50),
            source VARCHAR(100),
            extracted_date DATETIME,
            company_name VARCHAR(255),
            website VARCHAR(255),
            priority VARCHAR(50),
            notes TEXT,
            email_uid VARCHAR(255)
        )''')
        conn.commit()
    except Error as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn.is_connected():
            c.close()
            conn.close()


def exists(email):
    if email.startswith("__LAST_RUN__"):
        return False
    if email == SPECIAL_LAST_RUN_EMAIL:
        return False
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(f'SELECT 1 FROM {TABLE_NAME} WHERE email=%s AND email!=%s', (email, SPECIAL_LAST_RUN_EMAIL))
        result = c.fetchone()
        return result is not None
    except Error as e:
        print(f"Error checking existence: {e}")
        return False
    finally:
        if conn.is_connected():
            c.close()
            conn.close()

def insert(contact: Contact):
    if contact.email == SPECIAL_LAST_RUN_EMAIL:
        return
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            f'''INSERT IGNORE INTO {TABLE_NAME} 
            (email, name, phone, source, extracted_date, company_name, website, priority, notes, email_uid)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
            (
                contact.email,
                contact.name,
                contact.phone,
                contact.source,
                contact.extracted_date.strftime("%Y-%m-%d %H:%M:%S"),
                contact.company_name,
                contact.website,
                contact.priority,
                contact.notes,
                contact.email_uid
            )
        )
        conn.commit()
    except Error as e:
        print(f"Error inserting contact: {e}")
    finally:
        if conn.is_connected():
            c.close()
            conn.close()

def get_last_run_date():
    try:
        conn = get_connection()
        c = conn.cursor()
        # Get the latest extracted_date from all contacts except the special row
        c.execute(f"SELECT MAX(extracted_date) FROM {TABLE_NAME} WHERE email != %s", (SPECIAL_LAST_RUN_EMAIL,))
        row = c.fetchone()
        if row and row[0]:
            return row[0] 
        else:
            return None
    except Error as e:
        print(f"Error getting last run date: {e}")
        return None
    finally:
        if conn.is_connected():
            c.close()
            conn.close()

def get_last_run_date_for_account(account_email):
    special_email = f"__LAST_RUN__:{account_email}"
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(f"SELECT extracted_date FROM {TABLE_NAME} WHERE email=%s", (special_email,))
        row = c.fetchone()
        return row[0] if row and row[0] else None
    except Error as e:
        print(f"Error getting last run date for {account_email}: {e}")
        return None
    finally:
        if conn.is_connected():
            c.close()
            conn.close()

def update_last_run_date_for_account(account_email, dt):
    special_email = f"__LAST_RUN__:{account_email}"
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            f'''INSERT INTO {TABLE_NAME} (email, extracted_date)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE extracted_date=VALUES(extracted_date)''',
            (special_email, dt)
        )
        conn.commit()
    except Error as e:
        print(f"Error updating last run date for {account_email}: {e}")
    finally:
        if conn.is_connected():
            c.close()
            conn.close()
