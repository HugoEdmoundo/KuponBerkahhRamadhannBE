import sqlite3, uuid, random, string
from datetime import datetime
import pytz
from typing import Optional, Dict

def get_db():
    conn = sqlite3.connect('queue.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS periodes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warga (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            kk_number TEXT NOT NULL,
            rt_rw TEXT NOT NULL,
            referral_code TEXT NOT NULL UNIQUE,
            queue_number INTEGER NOT NULL,
            status TEXT DEFAULT 'waiting',
            created_at TEXT,
            updated_at TEXT,
            periode_id TEXT,
            FOREIGN KEY (periode_id) REFERENCES periodes (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS queue_settings (
            id TEXT PRIMARY KEY,
            current_queue_number INTEGER DEFAULT 0,
            current_referral_code TEXT DEFAULT '',
            next_queue_counter INTEGER DEFAULT 1,
            periode_id TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (periode_id) REFERENCES periodes (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_current_time():
    return datetime.now(pytz.timezone('Asia/Jakarta')).isoformat()

def get_active_periode() -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM periodes WHERE is_active = 1")
    periode = cursor.fetchone()
    conn.close()
    return dict(periode) if periode else None

def get_queue_settings(periode_id: str) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM queue_settings WHERE periode_id = ?", (periode_id,))
    settings = cursor.fetchone()
    conn.close()
    return dict(settings) if settings else None
