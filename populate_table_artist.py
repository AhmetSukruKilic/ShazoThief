#!/usr/bin/env python3
"""
populate_artists_no_english.py
‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
Adds NUM_ARTISTS random artists to the DB, **ensuring none of the names
exist in an English word list**.
"""

import sqlite3, random, string, os, sys, math
from pathlib import Path

DB_PATH      = Path(__file__).with_name("shazothief.db")
NUM_ARTISTS  = 100                       # tweak as you like
NAME_LENGTH  = 10

#Build a quick English dictionary
def load_english_words():
    # 1) Try the standard Unix word file
    word_file = Path("/usr/share/dict/words")
    if word_file.exists():
        with word_file.open() as f:
            return {w.strip().lower() for w in f if w[0].isalpha()}
    # 2) Fallback: a very small built-in list (okay for collision-avoidance)
    return {
        "the","of","to","and","a","in","is","it","you","that","he","was","for",
        "on","are","with","as","i","his","they","be","at","one","have","this"
    }

ENGLISH = load_english_words()

#Helpers
def random_str(n=NAME_LENGTH):
    """Random lowercase letters + digits."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

def is_english(word):
    return word.lower() in ENGLISH

def progress(i, total):
    filled = "▓" * math.floor(i / total * 20)
    empty  = "░" * (20 - len(filled))
    return f"[{filled}{empty}] {i}/{total} ({i/total:4.1%})"

#DB connection
conn = sqlite3.connect(DB_PATH)
c    = conn.cursor()
c.execute("PRAGMA foreign_keys = ON")

# Get the first free artist_id
start_id = c.execute("SELECT IFNULL(MAX(artist_id),0)+1 FROM artist").fetchone()[0]

# ── Generate & insert ───────────────────────────────────────────────────────
inserted = 0
while inserted < NUM_ARTISTS:
    name = random_str()
    # Keep regenerating if the candidate *is* a real English word
    while is_english(name):
        name = random_str()

    artist_id = start_id + inserted
    try:
        c.execute("INSERT INTO artist (artist_id, artist_name) VALUES (?,?)",
                  (artist_id, name))
        inserted += 1
        print("Artists", progress(inserted, NUM_ARTISTS), end="\r")
    except sqlite3.IntegrityError as err:
        # Extremely rare unless artist_id already exists
        print(f"\n⚠︎  Skipped id {artist_id}: {err}")
        artist_id += 1

conn.commit()
conn.close()
print("\n🎸  Finished inserting artists (all non-English names).")
