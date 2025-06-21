#!/usr/bin/env python3
"""
Adds per-user playlists + songs:

• 2 playlists per user   (rename or raise PLAYLISTS_PER_USER if you like)
• 10 random songs in each playlist  (SONGS_PER_PL needs no change)
• Safe to re-run: uses INSERT OR IGNORE everywhere
"""

import sqlite3, random, math
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).with_name("shazothief.db")

PLAYLISTS_PER_USER = 2
SONGS_PER_PL       = 10

def bar(i, total):
    done = "▓" * math.floor(i / total * 20)
    return f"[{done}{'░'*(20-len(done))}] {i}/{total} ({i/total:4.1%})"

conn = sqlite3.connect(DB_PATH)
c    = conn.cursor()
c.execute("PRAGMA foreign_keys = ON")

user_ids = [u for (u,) in c.execute("SELECT user_id FROM users")]
song_ids = [s for (s,) in c.execute("SELECT song_id FROM songs")]

if not user_ids or not song_ids:
    raise RuntimeError("Need users and songs populated first!")

# ── get next free playlist_id ────────────────────────────────────────────────
next_pid = c.execute("SELECT IFNULL(MAX(playlist_id),0)+1 FROM Playlist").fetchone()[0]

total_playlists = len(user_ids) * PLAYLISTS_PER_USER
created = 0

for uid in user_ids:
    for k in range(PLAYLISTS_PER_USER):
        pid  = next_pid; next_pid += 1
        name = f"{uid}_plist_{k+1}"
        now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1) generic Playlist row
        c.execute("INSERT OR IGNORE INTO Playlist (playlist_id) VALUES (?)", (pid,))
        # 2) concrete UserPlaylist row
        c.execute("""
            INSERT OR IGNORE INTO UserPlaylist
            (playlist_id, playlist_name, created_at, creator_id)
            VALUES (?,?,?,?)
        """, (pid, name, now, uid))

        # 3) pick random songs and link them
        chosen = random.sample(song_ids, min(SONGS_PER_PL, len(song_ids)))
        for sid in chosen:
            c.execute("""INSERT OR IGNORE INTO UserPlaylist_Song (playlist_id, song_id)
                         VALUES (?,?)""", (pid, sid))

        created += 1
        print("UserPlaylists", bar(created, total_playlists), end="\r")

conn.commit()
conn.close()
print("\n🎶  UserPlaylist + UserPlaylist_Song fully populated!")
