from datetime import datetime
import os
import sqlite3

from flask import flash, has_request_context

from user_methods import return_user_name

DB_PATH = os.path.join(os.path.dirname(__file__), "shazothief.db")

def _notify(msg):
        print(msg)

def create_blend(user1_id, user2_id):
    created_at = datetime.now()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if user1_id > user2_id:
        user1_id, user2_id = user2_id, user1_id
        
    user1_name = return_user_name(user1_id)
    user2_name = return_user_name(user2_id)
    
    blend_name = f"{user1_name} & {user2_name} Blend"
    
    if user1_id is None or user2_id is None:
        conn.close()
        print(f"One of the users does not exist: {user1_name}, {user2_name}")
        return
    if user1_id == user2_id:
        conn.close()
        print("Cannot create a blend with the same user.")
        _notify("Cannot create a blend with the same user.")
        return

    if check_blend_exists(user1_id, user2_id):
        conn.close()
        print(f"Blend already exists between {user1_name} and {user2_name}.")
        _notify(f"Blend already exists between {user1_name} and {user2_name}.")
        return
    
    cursor.execute("""
        INSERT INTO Playlist DEFAULT VALUES
    """)
    playlist_id = cursor.lastrowid
    
    # Insert new blend
    cursor.execute("""
        INSERT INTO BlendPlaylist (playlist_id, user1_id, user2_id, created_at, playlist_name)
        VALUES (?, ?, ?, ?, ?)
    """, (playlist_id, user1_id, user2_id, created_at, blend_name))
    conn.commit()
    conn.close()
    print(f"Blend created successfully: {blend_name} (ID: {playlist_id})")
    _notify(f"Blend created successfully: {blend_name} (ID: {playlist_id})")

def list_blends(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT b.playlist_id, b.blend_name, u1.username AS user1, u2.username AS user2, b.created_at
        FROM BlendPlaylist b
        JOIN users u1 ON b.user1_id = u1.user_id
        JOIN users u2 ON b.user2_id = u2.user_id
        WHERE b.user1_id = ? OR b.user2_id = ?
    """, (user_id, user_id))
    
    blends = cursor.fetchall()
    conn.close()
    return blends

def delete_blend(playlist_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM BlendPlaylist WHERE playlist_id = ?", (playlist_id,))
    conn.commit()
    
    conn.execute("DELETE FROM Playlist WHERE playlist_id = ?", (playlist_id,))
    conn.commit()
    
    conn.close()

def check_blend_exists(user1_id, user2_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 1 
        FROM blendplaylist 
        WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
    """, (user1_id, user2_id, user2_id, user1_id))
    
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def check_blend_exists_by_id(playlist_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM BlendPlaylist WHERE playlist_id = ?", (playlist_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def get_blend_songs(playlist_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if not check_blend_exists_by_id(playlist_id):
        conn.close()
        return []
    
    cursor.execute(""" 
        SELECT  song_id,
                title,
                artist,
                album,
                genre,
                duration_secs
        FROM (
            SELECT 0 AS prio,
                s.song_id,
                s.title,
                ar.artist_name   AS artist,
                al.title         AS album,
                s.genre,
                s.duration_secs
            FROM   BlendPlaylist b
            JOIN   LikedSongs l1 ON b.user1_id = l1.user_id
            JOIN   LikedSongs l2 ON b.user2_id = l2.user_id
            JOIN   songs      s  ON l1.song_id = s.song_id
            LEFT   JOIN artist ar ON s.artist_id = ar.artist_id
            LEFT   JOIN Album  al ON s.album_id  = al.album_id
            WHERE  b.playlist_id = ?
            AND  l1.song_id    = l2.song_id

            UNION ALL

            SELECT 1 AS prio,
                s.song_id,
                s.title,
                ar.artist_name,
                al.title,
                s.genre,
                s.duration_secs
            FROM   BlendPlaylist b
            JOIN   LikedSongs l1 ON b.user1_id = l1.user_id
            LEFT   JOIN   LikedSongs l2
                ON l2.user_id = b.user2_id
                AND l2.song_id = l1.song_id
            JOIN   songs s ON l1.song_id = s.song_id
            LEFT   JOIN artist ar ON s.artist_id = ar.artist_id
            LEFT   JOIN Album  al ON s.album_id  = al.album_id
            WHERE  b.playlist_id = ?
            AND  l2.song_id IS NULL

            UNION ALL

            SELECT 1 AS prio,
                s.song_id,
                s.title,
                ar.artist_name,
                al.title,
                s.genre,
                s.duration_secs
            FROM   BlendPlaylist b
            JOIN   LikedSongs l2 ON b.user2_id = l2.user_id
            LEFT   JOIN   LikedSongs l1
                ON l1.user_id = b.user1_id
                AND l1.song_id = l2.song_id
            JOIN   songs s ON l2.song_id = s.song_id
            LEFT   JOIN artist ar ON s.artist_id = ar.artist_id
            LEFT   JOIN Album  al ON s.album_id  = al.album_id
            WHERE  b.playlist_id = ?
            AND  l1.song_id IS NULL
        ) AS ranked
        ORDER BY prio, title
        LIMIT 20
    """, (playlist_id, playlist_id, playlist_id))
    
    
    songs = cursor.fetchall()
    conn.close()
    
    return [dict(r) for r in songs]