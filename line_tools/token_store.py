import sqlite3
import os

DB_PATH = "data/users.db"


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_token(user_id: str):
    """最新の user_id を1件だけ保存する"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # いったん全削除してから1件だけ保存
    c.execute("DELETE FROM users")
    c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def load_token():
    """最後に保存した user_id を1件だけ取得する"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row[0] if row else None
