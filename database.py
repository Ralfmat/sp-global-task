import sqlite3
import dotenv
import os
from dotenv import load_dotenv

load_dotenv()

# db_name = os.environ.get("DB_NAME")
db_name = "contacts.db"


def get_db_connection():
    return sqlite3.connect(db_name, timeout=10.0)

def init_db():
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                phone TEXT UNIQUE NOT NULL
            )
        ''')
        connection.commit()
    finally:
        connection.close()

def add_contact(name: str, phone: str) -> dict:
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO contacts (name, phone) VALUES (?, ?)", (name, phone))
        connection.commit()
        return {"success": True, "name": name, "phone": phone}
    
    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if "contacts.name" in error_msg:
            return {"success": False, "error": f"Contact name '{name}' already exists."}
        elif "contacts.phone" in error_msg:
            return {"success": False, "error": f"Phone number '{phone}' is already assigned to someone else."}
        else:
            return {"success": False, "error": "Database integrity error."}
    finally:
        connection.close()

def get_contact(name: str) -> dict:
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT name, phone FROM contacts WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if result:
            return {"success": True, "name": result[0], "phone": result[1]}
        return {"success": False, "error": f"Contact '{name}' not found."}
    finally:
        connection.close()

def get_all_contacts() -> dict:
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT name, phone FROM contacts")
        results = cursor.fetchall()
        contacts = [{"name": row[0], "phone": row[1]} for row in results]
        return {"success": True, "data": contacts}
    finally:
        connection.close()

def delete_contact(name: str) -> dict:
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM contacts WHERE name = ?", (name,))
        changes = connection.total_changes
        connection.commit()
        
        if changes > 0:
            return {"success": True, "name": name, "message": "Contact deleted successfully."}
        return {"success": False, "error": f"Contact '{name}' does not exist."}
    finally:
        connection.close()

def update_contact(name: str, new_phone: str) -> dict:
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE contacts 
            SET phone = ? 
            WHERE name = ?
        ''', (new_phone, name))
        changes = connection.total_changes
        connection.commit()
        
        if changes > 0:
            return {"success": True, "name": name, "new_phone": new_phone}
        return {"success": False, "error": f"Contact '{name}' not found."}
    except sqlite3.IntegrityError:
        return {"success": False, "error": f"The phone number '{new_phone}' is already in use."}
    finally:
        connection.close()

init_db()