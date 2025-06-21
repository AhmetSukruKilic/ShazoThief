import sqlite3
import os
from flask import has_request_context
from flask import flash
from search_audio import match_query_clip
from artist_methods import returnArtistID, createNewArtist
from song_methods import isValidSongArtistID_Title
from volume_editor_methods import hash_music

DB_PATH = os.path.join(os.path.dirname(__file__), "shazothief.db")

def _notify(msg):
    """Flash in a web request, print otherwise."""
    if has_request_context():
        flash(msg)
    else:
        print(msg)
        
        
def insert_song_metadata(title, artist_id, duration_secs, album_id, path, genre, c, conn):
    c.execute(
        "SELECT song_id FROM songs WHERE title = ? AND artist_id = ?;",
        (title, artist_id)
    )
    row = c.fetchone()
    if row:
        return row[0]

    c.execute(
        """
        INSERT INTO songs
            (title, artist_id, duration_secs, album_id, path, genre)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (title, artist_id, duration_secs, album_id, path, genre)
    )
    conn.commit()
    song_id = c.lastrowid
    return song_id

def fingerprint_and_store(duration_secs, hashes_q, title, artist_id, album_id, path, genre, c, conn):
    song_id = insert_song_metadata(title, artist_id, duration_secs, album_id, path, genre, c, conn)
    for hval, toff in hashes_q:
        c.execute(
            """
            INSERT OR IGNORE INTO fingerprints
                (song_id, hash_value, time_offset)
            VALUES (?, ?, ?);
            """,
            (song_id, hval, toff)
        )
    conn.commit()

def registerSong(path, title, artist_name, album_title=None, genre="Unknown"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    artist_id = returnArtistID(artist_name, c)
    if artist_id is None:
        print(f"New Artist: {artist_name}")
        _notify(f"New Artist: {artist_name}")
        createNewArtist(artist_name, c, conn)
        artist_id = returnArtistID(artist_name, c)

    album_id = None
    if album_title:
        c.execute("SELECT album_id FROM album WHERE title = ?", (album_title,))
        row = c.fetchone()
        if row:
            album_id = row[0]
        else:
            c.execute(
                "INSERT INTO album (title, artist_id) VALUES (?, ?)",
                (album_title, artist_id)
            )
            album_id = c.lastrowid
            print(f"New Album: {album_title}")
            _notify(f"New Album: {album_title}")
            conn.commit()

    if not isValidSongArtistID_Title(artist_id, title, c):
        print(f"The song is already exist: {artist_name} - {title}")
        _notify(f"The song is already exist: {artist_name} - {title}")
        conn.close()
        return

    mathced_id, mathced_offset = match_query_clip(path, c)
    
    if mathced_id is not None:
        print(f"Same song already in database matched_offset: {mathced_offset} frame)")
        _notify(f"Same song already in database matched_offset: {mathced_offset} frame)")
        conn.close()
        return
    
    duration_secs, hashes_q = hash_music(path)

    fingerprint_and_store(
        duration_secs,
        hashes_q,
        title,
        artist_id,
        album_id,
        path,
        genre,
        c,
        conn
    )
    print(f"New Song added: {artist_name} - {title}")
    _notify(f"New Song added: {artist_name} - {title}")
    conn.close()