import mysql.connector
from mysql.connector import Error
from models.contact import Contact
import os
from datetime import datetime, timedelta

DB_HOST = os.getenv("DB_HOST", "35.232.56.51")
DB_USER = os.getenv("DB_USER", "xccscsa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Innovapath1")
DB_NAME = os.getenv("DB_NAME", "ajwjww")
DB_PORT = int(os.getenv("PORT", 3306))

TABLE_NAME = "contacts_extractor"
META_TABLE = "meta"

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
        c.execute(f'''CREATE TABLE IF NOT EXISTS {META_TABLE} (
            `key` VARCHAR(255) PRIMARY KEY,
            `value` VARCHAR(255)
        )''')
        conn.commit()
    except Error as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn.is_connected():
            c.close()
            conn.close()

def exists(email):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(f'SELECT 1 FROM {TABLE_NAME} WHERE email=%s', (email,))
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
        c.execute(f'SELECT value FROM {META_TABLE} WHERE `key`=%s', ("last_run",))
        row = c.fetchone()
        if row:
            return datetime.fromisoformat(row[0])
        else:
            return datetime.now() - timedelta(days=365)  # Default: 1 year ago
    except Error as e:
        print(f"Error getting last run date: {e}")
        return datetime.now() - timedelta(days=365)
    finally:
        if conn.is_connected():
            c.close()
            conn.close()

def update_last_run_date(dt):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            f'INSERT INTO {META_TABLE} (`key`, `value`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE `value`=VALUES(`value`)',
            ("last_run", dt.isoformat())
        )
        conn.commit()
    except Error as e:
        print(f"Error updating last run date: {e}")
    finally:
        if conn.is_connected():
            c.close()
            conn.close()