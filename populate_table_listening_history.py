import sqlite3, random, math
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).with_name("shazothief.db")
HISTORY_PER_USER = 10  # Change as needed

def bar(i, total):
    done = "▓" * math.floor(i / total * 20)
    todo = "░" * (20 - len(done))
    return f"[{done}{todo}] {i}/{total} ({i/total:4.1%})"

def random_timestamp(within_days=30):
    now = datetime.now()
    offset = timedelta(days=random.randint(0, within_days),
                       hours=random.randint(0, 23),
                       minutes=random.randint(0, 59),
                       seconds=random.randint(0, 59))
    return (now - offset).strftime("%Y-%m-%d %H:%M:%S")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON")

user_ids = [uid for (uid,) in c.execute("SELECT user_id FROM users")]
song_ids = [sid for (sid,) in c.execute("SELECT song_id FROM songs")]

if not user_ids or not song_ids:
    raise RuntimeError("Missing users or songs — can't generate history.")

total_ops = len(user_ids) * HISTORY_PER_USER
op_count = 0

for uid in user_ids:
    chosen_songs = random.sample(song_ids, min(HISTORY_PER_USER, len(song_ids)))
    for sid in chosen_songs:
        timestamp = random_timestamp()
        c.execute("""
            INSERT OR IGNORE INTO ListeningHistory (user_id, song_id, time_stamp)
            VALUES (?, ?, ?)
        """, (uid, sid, timestamp))

        op_count += 1
        if op_count % 10 == 0 or op_count == total_ops:
            print("History", bar(op_count, total_ops), end="\r")

conn.commit()
conn.close()
print("\n🎧  Listening history populated.")
