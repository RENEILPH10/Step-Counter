import sqlite3
class Database:
    def __init__(self, path="records.db"):
        self.path = path
        self.conn = None
    def init_db(self):
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dt TEXT NOT NULL,
                distance_km REAL NOT NULL,
                speed_kmh REAL NOT NULL,
                steps INTEGER NOT NULL
            )
        """)
        self.conn.commit()
    def insert_record(self, dt, distance_km, speed_kmh, steps):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO records (dt, distance_km, speed_kmh, steps) VALUES (?, ?, ?, ?)", (dt, distance_km, speed_kmh, steps))
        self.conn.commit()
    def fetch_records(self, limit=100):
        cur = self.conn.cursor()
        cur.execute("SELECT dt, distance_km, speed_kmh, steps FROM records ORDER BY id DESC LIMIT ?", (limit,))
        return cur.fetchall()
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
