#!/usr/bin/env python3
"""
populate_liked_songs.py
‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
Random-fills the LikedSongs table.

• One quick pass: every user gets 10 random “likes”.
• Uses INSERT OR IGNORE, so rerunning is safe.
"""

import sqlite3, random, math
from pathlib import Path

DB_PATH        = Path(__file__).with_name("shazothief.db")
LIKES_PER_USER = 5         # tweak as you like

def bar(i, total):
    done  = "▓" * math.floor(i / total * 20)
    todo  = "░" * (20 - len(done))
    return f"[{done}{todo}] {i}/{total} ({i/total:4.1%})"

conn = sqlite3.connect(DB_PATH)
c    = conn.cursor()
c.execute("PRAGMA foreign_keys = ON")

# --- fetch basic data --------------------------------------------------------
user_ids  = [uid for (uid,) in c.execute("SELECT user_id FROM users")]
song_ids  = [sid for (sid,) in c.execute("SELECT song_id FROM songs")]

if not user_ids or not song_ids:
    raise RuntimeError("Users or songs table is empty — nothing to like!")

total_ops = len(user_ids) * LIKES_PER_USER
op_count  = 0

# --- main loop ---------------------------------------------------------------
for uid in user_ids:
    picks = random.sample(song_ids, min(LIKES_PER_USER, len(song_ids)))
    for sid in picks:
        c.execute("""
            INSERT OR IGNORE INTO LikedSongs (user_id, song_id)
            VALUES (?, ?)
        """, (uid, sid))

        op_count += 1
        if op_count % 5 == 0 or op_count == total_ops:
            print("LikedSongs", bar(op_count, total_ops), end="\r")

conn.commit()
conn.close()
print("\n❤️  All likes inserted!")
