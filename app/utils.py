from dotenv import load_dotenv
import time
import os
from fastapi import FastAPI, HTTPException, Header, Depends, Request
import sqlite3
from app.models import MessageOut, Message
from datetime import datetime
from collections import defaultdict

load_dotenv()


rate_limits = defaultdict(lambda: [])

RATE_LIMIT = int(os.getenv("RATE_LIMIT", 100))
RATE_WINDOW = int(os.getenv("RATE_WINDOW", 60))
DB_FILE = os.getenv("DB_FILE")

def check_rate_limit(ip):
    now = time.time()
    rate_limits[ip] = [t for t in rate_limits[ip] if now - t < RATE_WINDOW]
    if len(rate_limits[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    rate_limits[ip].append(now)

def to_message_out(row):
    if row[0] is None:
        message_id = ""
    else:
        message_id = row[0]
    return MessageOut(
        id = message_id, 
        sender=row[1],
        content=row[2],
        timestamp=datetime.fromisoformat(row[3]).timestamp()
    )

async def add_message_internal(
    sid: str,
    sender: str,
    content: str
) -> Message:
    timestamp = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_FILE) as conn:
        print("SID ", sid)
        cursor = conn.execute(
            "INSERT INTO messages (id, session_id, sender, content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (str(sid + "-" + str(int(timestamp.split(".")[-1]))), sid, sender, content, timestamp),
        )
        conn.commit()
        message_id = str(cursor.lastrowid)
    return Message(id=message_id, sender=sender, content=content, timestamp=timestamp)

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            name TEXT,
            is_favorite BOOLEAN
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            sender TEXT,
            content TEXT,
            context TEXT,
            timestamp REAL,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )''')