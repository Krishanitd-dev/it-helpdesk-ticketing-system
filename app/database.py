import os
import psycopg
from dotenv import load_dotenv
from datetime import datetime
from app.auth import secure_hash

load_dotenv()

DATABASE = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg.connect(DATABASE)

def create_user_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS userdata (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def create_user(email, password_hash, created_at):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO userdata (email, password_hash, created_at)
        VALUES (%s, %s, %s)
        """, (email, password_hash, created_at))
    conn.commit()
    cursor.close()
    conn.close()
    

def get_user(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, email, password_hash, created_at
        FROM userdata 
        WHERE email = %s
        """, (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return user

def create_test_user():
    conn = get_connection()
    cursor = conn.cursor()
    password_hash = secure_hash("user123")
    created_at = datetime.now()
    cursor.execute("""
        INSERT INTO userdata (email, password_hash, created_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO NOTHING
        """, ("user1@test.com", password_hash, created_at)
    )
    conn.commit()
    cursor.close()
    conn.close()

def create_ticket_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(""" CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY, 
    user_id INTEGER NOT NULL, 
    subject VARCHAR(255) NOT NULL, 
    category VARCHAR(100) NOT NULL, 
    priority VARCHAR(50) NOT NULL, 
    description TEXT NOT NULL, 
    status VARCHAR(50) NOT NULL DEFAULT 'Open', 
    response TEXT, 
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ) """)

    conn.commit()
    cursor.close()
    conn.close()

def get_ticket_counts(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'Open') AS open,
            COUNT(*) FILTER (WHERE status = 'Closed') AS closed
        FROM tickets
        WHERE user_id = %s
    """, (user_id,))

    counts = cursor.fetchone()

    cursor.close()
    conn.close()

    return counts

def get_dashboard_data(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) FILTER (WHERE status = 'Open') AS open_tickets,
            COUNT(*) FILTER (WHERE status = 'In Progress') AS in_progress_tickets,
            COUNT(*) FILTER (WHERE status = 'Closed') AS closed_tickets
        FROM tickets
        WHERE user_id = %s
    """, (user_id,))

    counts = cursor.fetchone()
    cursor.execute("""
        SELECT id, subject, category, priority, status, created_at
        FROM tickets
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 5
    """, (user_id,))
    recent_tickets = cursor.fetchall()
    cursor.close()
    conn.close()
    return counts, recent_tickets

def create_helpdesk_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS helpdesk_users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

def create_test_helpdesk():
    conn = get_connection()
    cursor = conn.cursor()

    password_hash = secure_hash("Admin123")

    cursor.execute("""
        INSERT INTO helpdesk_users (
            email,
            password_hash
        )
        VALUES (%s, %s)
        ON CONFLICT (email) DO NOTHING
    """, (
        "admin@helpdesk.com",
        password_hash
    ))

    conn.commit()
    cursor.close()
    conn.close()

def get_helpdesk_user(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, email, password_hash, created_at
        FROM helpdesk_users
        WHERE email = %s
    """, (email,))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user

def get_all_tickets():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            tickets.id,
            tickets.subject,
            tickets.category,
            tickets.priority,
            tickets.status,
            tickets.created_at,
            userdata.email
        FROM tickets
        JOIN userdata
            ON tickets.user_id = userdata.id
        ORDER BY tickets.created_at DESC
    """)

    tickets = cursor.fetchall()

    cursor.close()
    conn.close()

    return tickets