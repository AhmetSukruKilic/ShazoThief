def returnArtistID(artist_name, c):
    c.execute(
        """
        SELECT artist_id
        FROM Artist
        WHERE artist_name = ?
        """,
        (artist_name,)
    )

    result = c.fetchone()
    return result[0] if result else None

def returnArtistName(artist_id, c):
    c.execute(
        """
        SELECT artist_name
        FROM Artist
        WHERE artist_id = ?
        """,
        (artist_id,)
    )

    result = c.fetchone()
    return result[0] if result else None

def createNewArtist(artist_name, c, conn):
    c.execute(
        """
        INSERT INTO Artist (artist_name)
        VALUES (?);
        """,
        (artist_name,)
    )
    conn.commit()
    return returnArtistID(artist_name, c)



