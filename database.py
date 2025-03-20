import sqlite3

def create_database():
    conn = sqlite3.connect("chat_log.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_input TEXT,
            bot_response TEXT
        )
    """)
    conn.commit()
    conn.close()

create_database()
