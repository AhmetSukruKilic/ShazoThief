import sqlite3, random, math
from pathlib import Path
from datetime import datetime

DB_PATH     = Path(__file__).with_name("shazothief.db")
MAX_PAIRS   = 1000         # overall hard cap
PARTNERS_PER_USER = 5      # ← change here if you want a different limit

def bar(i, total):
    done = "▓" * math.floor(i / total * 20)
    return f"[{done}{'░'*(20-len(done))}] {i}/{total} ({i/total:4.1%})"

conn = sqlite3.connect(DB_PATH)
c    = conn.cursor()
c.execute("PRAGMA foreign_keys = ON")

# ── collect users ────────────────────────────────────────────────────────────
user_ids = sorted(uid for (uid,) in c.execute("SELECT user_id FROM users"))

# Build pair list: each u1 gets at most 5 unique u2 (> u1)
pairs = []
for u1 in user_ids:
    partners = [u2 for u2 in user_ids if u2 > u1]
    random.shuffle(partners)                    # optional: mix it up
    pairs.extend((u1, u2) for u2 in partners[:PARTNERS_PER_USER])
    if len(pairs) >= MAX_PAIRS:                 # respect overall cap
        pairs = pairs[:MAX_PAIRS]
        break

# ── get next playlist_id ─────────────────────────────────────────────────────
next_pid = c.execute("SELECT IFNULL(MAX(playlist_id),0)+1 FROM Playlist").fetchone()[0]

for i, (u1, u2) in enumerate(pairs, start=1):
    pid = next_pid + i - 1
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        c.execute("INSERT INTO Playlist (playlist_id) VALUES (?)", (pid,))
        c.execute("""
            INSERT INTO BlendPlaylist
                  (playlist_id, playlist_name, created_at, user1_id, user2_id)
            VALUES (?, ?, ?, ?, ?)
        """, (pid, f"Blend_{u1}_{u2}", now, u1, u2))
        print("BlendPlaylist", bar(i, len(pairs)), end="\r")
    except sqlite3.IntegrityError as e:
        print(f"\n⚠ Skipped pair ({u1},{u2}): {e}")

conn.commit()
conn.close()
print("\n🤝  Blend playlists inserted.")
