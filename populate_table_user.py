import sqlite3, random, string, math
from pathlib import Path

DB_PATH = Path(__file__).with_name("shazothief.db")
NUM_USERS = 1000

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON")

def bar(i, tot):
    done = "▓" * math.floor(i / tot * 20)
    todo = "░" * (20 - len(done))
    return f"[{done}{todo}] {i}/{tot} ({i/tot:4.1%})"

def rndstr(n):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

for i in range(1, NUM_USERS + 1):
    uname = rndstr(8)
    email = f"{rndstr(5)}@{rndstr(4)}.com"
    phone = "+90" + ''.join(random.choices("0123456789", k=10))
    pw    = rndstr(10)
    admin = 1 if i == 1 else 0

    c.execute("""
        INSERT OR IGNORE INTO users
        (user_id, username, password, email, phone_number, is_admin)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (i, uname, pw, email, phone, admin))

    print("Users", bar(i, NUM_USERS), end="\r")

conn.commit()
conn.close()
print("\n✅  Random users inserted.")
