from collections import Counter
import sqlite3

from flask import flash, has_request_context
from volume_editor_methods import hash_music
from artist_methods import returnArtistName
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "shazothief.db")
MIN_COUNT = 10

def _notify(msg):
    """Flash in a web request, print otherwise."""
    if has_request_context():
        flash(msg)
    else:
        print(msg)
        
def hash_check_query_clip(query_filepath, c):
    duration_secs, hashes_q = hash_music(query_filepath)
    
    if not hashes_q:
        return None
    
    hashes_q = hashes_q[:500]
    
    matches = []  # will store tuples (song_id, delta_time)
    for (hval, q_time) in hashes_q:
        c.execute("""
            SELECT song_id, time_offset
            FROM fingerprints
            WHERE hash_value = ?
        """, (hval,))
        rows = c.fetchall()
        for (db_song_id, db_time_offset) in rows:
            delta = db_time_offset - q_time
            matches.append((db_song_id, delta))
    return matches

def match_query_clip(query_filepath, c):
    matches = hash_check_query_clip(query_filepath, c)

    counter = Counter(matches)
    if not counter:
        return None, None

    (best_song_id, best_delta), count = counter.most_common(1)[0]

    if count < MIN_COUNT:
        return None, None

    return best_song_id, best_delta

def search_audio(link):
    """Search for a song by matching a short audio clip against the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    best_song_id, best_offset = match_query_clip(link, c)

    if best_song_id is not None:
        c.execute("""
            SELECT title, artist_id
            FROM songs 
            WHERE song_id = ?
        """, (best_song_id,))
        title, artist_id = c.fetchone()
        artist_name = returnArtistName(artist_id, c)
        print(f"Matched song: {title} - {artist_name} (offset: {best_offset} frame)")
        _notify(f"Matched song: {title} - {artist_name} (offset: {best_offset} frame)")
    else:
        print("No matching song found.")
        _notify("No matching song found.")
    conn.commit()
    conn.close()
