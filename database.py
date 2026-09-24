import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "chronolit.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        source_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id INTEGER,
        event_date TEXT,
        event_text TEXT,
        cluster_id INTEGER,
        FOREIGN KEY(topic_id) REFERENCES topics(id)
    )
    """)
    conn.commit()
    conn.close()

def save_topic(topic: str, source_url: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO topics(topic, source_url) VALUES (?, ?)",
        (topic, source_url)
    )
    topic_id = cur.lastrowid
    conn.commit()
    conn.close()
    return topic_id

def save_events(topic_id: int, events: List[Dict[str, Any]]):
    conn = get_connection()
    cur = conn.cursor()
    for e in events:
        date_value = (
            e["date"].isoformat()
            if hasattr(e.get("date"), "isoformat") and e["date"]
            else (str(e["date"]) if e.get("date") else None)
        )
        cur.execute("""
        INSERT INTO events(topic_id, event_date, event_text, cluster_id)
        VALUES (?, ?, ?, ?)
        """, (
            topic_id,
            date_value,
            e.get("text", ""),
            e.get("cluster", -1)
        ))
    conn.commit()
    conn.close()

def get_all_topics() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT t.id, t.topic, t.source_url, t.created_at, COUNT(e.id) as event_count
    FROM topics t
    LEFT JOIN events e ON t.id = e.topic_id
    GROUP BY t.id
    ORDER BY t.id DESC
    """)
    rows = cur.fetchall()
    topics = [dict(row) for row in rows]
    conn.close()
    return topics

def get_topic_timeline(topic_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, topic, source_url, created_at FROM topics WHERE id = ?", (topic_id,))
    topic_row = cur.fetchone()
    if not topic_row:
        conn.close()
        return None
    
    cur.execute("""
    SELECT id, event_date, event_text, cluster_id
    FROM events
    WHERE topic_id = ?
    ORDER BY id ASC
    """, (topic_id,))
    event_rows = cur.fetchall()
    conn.close()
    
    events = []
    for r in event_rows:
        year_val = None
        if r["event_date"]:
            try:
                year_val = int(r["event_date"].split("-")[0])
            except Exception:
                year_val = r["event_date"]
        events.append({
            "id": r["id"],
            "date": year_val,
            "text": r["event_text"],
            "cluster": r["cluster_id"]
        })
        
    return {
        "id": topic_row["id"],
        "topic": topic_row["topic"],
        "source": topic_row["source_url"],
        "created_at": topic_row["created_at"],
        "events": events
    }
