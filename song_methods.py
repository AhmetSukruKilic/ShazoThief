from flask import flash, has_request_context

def _notify(msg):
    if has_request_context():
        flash(msg)
    else:
        print(msg)
        
def isValidSongArtistID_Title(artist_id, title, c):
    c.execute(
        """
        SELECT 1
        FROM songs
        WHERE title = ? AND artist_id = ?
        """,
        (title, artist_id)
    )
    result = c.fetchall()
    return len(result) == 0

def deleteSong(song_id, c, conn):
    """
    Delete a song from all related tables in the database.
    """
    c.execute("SELECT title FROM songs WHERE song_id = ?", (song_id,))
    row = c.fetchone()
    song_title = row[0] if row else None
    
    c.execute("DELETE FROM LikedSongs WHERE song_id = ?", (song_id,))
    c.execute("DELETE FROM fingerprints WHERE song_id = ?", (song_id,))
    c.execute("DELETE FROM UserPlaylist_Song WHERE song_id = ?", (song_id,))
    c.execute("DELETE FROM ListeningHistory WHERE song_id = ?", (song_id,))
    c.execute("DELETE FROM songs WHERE song_id = ?", (song_id,))
    conn.commit()
    
    try:
        flash(f"🗑️ Song with ID {song_id} and Title {song_title} deleted from liked_songs, fingerprints, playlist_songs, and songs.")
    except RuntimeError:
        print(f"🗑️ Song with ID {song_id} and Title {song_title} deleted from liked_songs, fingerprints, playlist_songs, and songs.")

def listGenreCounts(c):
    """
    List the count of songs for each genre.
    """
    c.execute("""
        SELECT genre, COUNT(*) AS count
        FROM songs
        GROUP BY genre
        ORDER BY count DESC
    """)
    return c.fetchall()