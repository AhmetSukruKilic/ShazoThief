import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "shazothief.db")


def create_user_playlist(playlist_name, creator_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.now()
    # Insert into Playlist to get a new playlist_id
    cur.execute("""
        INSERT INTO Playlist DEFAULT VALUES
    """)
    playlist_id = cur.lastrowid
    # Insert into UserPlaylist with the new playlist_id as a foreign key
    cur.execute("""
        INSERT INTO UserPlaylist (playlist_id, playlist_name, created_at, creator_id)
        VALUES (?, ?, ?, ?)
    """, (playlist_id, playlist_name, now, creator_id))
    conn.commit()
    conn.close()
    return playlist_id


def add_song_to_user_playlist(playlist_id, song_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO UserPlaylist_Song (playlist_id, song_id)
        VALUES (?, ?)
    """, (playlist_id, song_id))

    conn.commit()
    conn.close()

    print(f"Song {song_id} added to user playlist {playlist_id}.")

def list_songs_in_user_playlist(playlist_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute("""
      SELECT
        s.song_id,
        s.title,
        ar.artist_name AS artist,
        al.title       AS album,
        s.genre,
        s.duration_secs
      FROM UserPlaylist_Song ups
      JOIN songs s  ON ups.song_id   = s.song_id
      LEFT JOIN artist ar ON s.artist_id = ar.artist_id
      LEFT JOIN Album  al ON s.album_id   = al.album_id
      WHERE ups.playlist_id = ?
      ORDER BY s.title
    """, (playlist_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def remove_song_from_user_playlist(playlist_id, song_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM UserPlaylist_Song
        WHERE playlist_id = ? AND song_id = ?
    """, (playlist_id, song_id))

    conn.commit()
    conn.close()

    print(f"Song {song_id} removed from playlist {playlist_id}.")

def delete_user_playlist(playlist_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM UserPlaylist_Song WHERE playlist_id = ?
    """, (playlist_id,))

    cursor.execute("""
        DELETE FROM UserPlaylist WHERE playlist_id = ?
    """, (playlist_id,))

    cursor.execute("""
        DELETE FROM Playlist WHERE playlist_id = ?
    """, (playlist_id,))
    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print(f"User playlist {playlist_id} deleted.")



