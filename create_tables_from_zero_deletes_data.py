import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "shazothief.db")
conn = sqlite3.connect(DB_PATH)

cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")

drop_script = """
DROP TABLE IF EXISTS ListeningHistory;
DROP TABLE IF EXISTS LikedSongs;
DROP TABLE IF EXISTS UserPlaylist_Song;
DROP TABLE IF EXISTS UserPlaylist;
DROP TABLE IF EXISTS BlendPlaylist;
DROP TABLE IF EXISTS playlist;
DROP TABLE IF EXISTS fingerprints;
DROP TABLE IF EXISTS songs;
DROP TABLE IF EXISTS album;
DROP TABLE IF EXISTS artist;
DROP TABLE IF EXISTS users;
"""


create_script = """
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username VARCHAR(100),
    password VARCHAR(100),
    email VARCHAR(100),
    phone_number VARCHAR(20),
    is_admin BOOLEAN,
    UNIQUE(username)
);

CREATE TABLE artist (
    artist_id INTEGER PRIMARY KEY,
    artist_name VARCHAR(100)
);

CREATE TABLE Album (
    album_id INTEGER PRIMARY KEY,
    title VARCHAR(100),
    artist_id INTEGER,
    FOREIGN KEY (artist_id) REFERENCES artist(artist_id)
);

CREATE TABLE songs (
    song_id INTEGER PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    genre VARCHAR(50),
    duration_secs INTEGER NOT NULL,
    album_id INTEGER,
    artist_id INTEGER NOT NULL,
    path VARCHAR(500),
    UNIQUE(title, artist_id),
    FOREIGN KEY (album_id) REFERENCES Album(album_id),
    FOREIGN KEY (artist_id) REFERENCES artist(artist_id)
);

CREATE TABLE UserPlaylist (
    playlist_id INTEGER PRIMARY KEY,
    playlist_name VARCHAR(100),
    created_at TIMESTAMP,
    creator_id INTEGER NOT NULL,
    FOREIGN KEY (creator_id) REFERENCES users(user_id)
    FOREIGN KEY (playlist_id) REFERENCES Playlist(playlist_id)
);

create table Playlist (
    playlist_id INTEGER PRIMARY KEY
);

CREATE TABLE BlendPlaylist (
    playlist_id INTEGER PRIMARY KEY,
    playlist_name VARCHAR(100),
    created_at TIMESTAMP,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    UNIQUE (user1_id, user2_id),
    FOREIGN KEY (playlist_id) REFERENCES Playlist(playlist_id),
    FOREIGN KEY (user1_id) REFERENCES users(user_id),
    FOREIGN KEY (user2_id) REFERENCES users(user_id),
    CHECK (user1_id < user2_id)
);  

CREATE TABLE UserPlaylist_Song (
    playlist_id INTEGER NOT NULL,
    song_id INTEGER NOT NULL,
    PRIMARY KEY (playlist_id, song_id),
    FOREIGN KEY (playlist_id) REFERENCES UserPlaylist(playlist_id),
    FOREIGN KEY (song_id) REFERENCES songs(song_id)
);

CREATE TABLE LikedSongs (
    user_id INTEGER,
    song_id INTEGER,
    PRIMARY KEY (user_id, song_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (song_id) REFERENCES songs(song_id)
);

CREATE TABLE ListeningHistory (
    user_id INTEGER,
    song_id INTEGER,
    time_stamp TIMESTAMP,
    PRIMARY KEY (user_id, song_id, time_stamp),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (song_id) REFERENCES songs(song_id)
);

CREATE TABLE fingerprints (
    song_id INTEGER NOT NULL,
    hash_value INTEGER NOT NULL ,
    time_offset INTEGER NOT NULL,
    PRIMARY KEY (song_id, time_offset),
    FOREIGN KEY (song_id) REFERENCES songs(song_id)
);

CREATE INDEX idx_fingerprints_hash_value
        ON fingerprints(hash_value);
"""

cursor.executescript(drop_script)
cursor.executescript(create_script)

conn.commit()
conn.close()

print("Database has created")
