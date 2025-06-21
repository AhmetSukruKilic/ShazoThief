import blend_methods
from playlist_methods import *
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import sqlite3
import os
from load_audio import registerSong
from search_audio import match_query_clip
from song_methods import deleteSong, listGenreCounts
from user_methods import signUser
# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

UPLOAD_FOLDER    = os.path.join(os.path.dirname(__file__), "static", "Songs")
ALLOWED_EXTENSIONS = {"wav", "mp3"}
DB_PATH = os.path.join(os.path.dirname(__file__), "shazothief.db")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------------------------------------------------------
# ROUTES
# -----------------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and user["password"] == password:
            session.clear()  # Eski kullanıcı verileri silinir
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["is_admin"] = user["is_admin"]

            if user["is_admin"]:
                return redirect(url_for("admin_home"))  # admin home page
            else:
                return redirect(url_for("user_home"))  # user home page
        else:
            flash("Invalid username or password", "danger")

    return render_template("index.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()

        if not username or not password:
            flash('Username and password required.', 'warning')
            return redirect(url_for('signup'))

        signUser(username, password, email, phone)
        flash('Signup successful. You can now log in.', 'success')
        return redirect(url_for('index'))

    return render_template('signup.html')



@app.route("/admin")
def admin_home():
    if not session.get("is_admin"):
        return redirect(url_for("index"))

    conn   = get_db_connection()
    cursor = conn.cursor()

    # Expected shape: [("Pop", 42), ("Rock", 17), ...]
    genres = listGenreCounts(cursor)

    conn.close()

    total_songs = sum(count for _, count in genres)  # for % display
    return render_template(
        "admin_home.html",
        genres=genres,
        total_songs=total_songs
    )

# list & delete view
@app.route("/admin/songs")
def admin_songs():                                     
    conn = get_db_connection()
    cur  = conn.cursor()
    songs = cur.execute(
        "SELECT song_id, title, genre FROM songs ORDER BY song_id DESC"
    ).fetchall()
    conn.close()
    return render_template("admin_songs.html", songs=songs)

# delete handler
@app.route("/admin/songs/<int:song_id>/delete", methods=["POST"])
def delete_song(song_id):
    conn   = get_db_connection()
    cursor = conn.cursor()
    deleteSong(song_id, cursor, conn)                  
    conn.close()
    return redirect(url_for("admin_songs"))

@app.route("/user")
def user_home():
    if "user_id" not in session:
        return redirect(url_for("index"))

    conn = get_db_connection()
    user_id = session["user_id"]

    # COMPLEX + fallback recent_songs
    recent_songs = conn.execute("""
        SELECT 
            s.song_id,
            s.title,
            ar.artist_name,
            al.title AS album,
            COUNT(*) AS listen_count,
            MAX(lh.time_stamp) AS last_listened
        FROM ListeningHistory lh
        JOIN songs s ON lh.song_id = s.song_id
        LEFT JOIN artist ar ON s.artist_id = ar.artist_id
        LEFT JOIN Album al ON s.album_id = al.album_id
        WHERE lh.user_id = ?
        GROUP BY s.song_id
        ORDER BY last_listened DESC
        LIMIT 10;
    """, (user_id,)).fetchall()

    # Fallback: yeni kullanıcı için
    if not recent_songs:
        recent_songs = conn.execute("""
            SELECT 
                s.song_id,
                s.title,
                ar.artist_name,
                al.title AS album,
                0 AS listen_count,
                NULL AS last_listened
            FROM songs s
            LEFT JOIN artist ar ON s.artist_id = ar.artist_id
            LEFT JOIN Album al ON s.album_id = al.album_id
            ORDER BY RANDOM()
            LIMIT 5;
        """).fetchall()

    # current_song ayarlanması
    if not session.get('current_song') and recent_songs:
        first_id = recent_songs[0]['song_id']
        song = conn.execute("""
            SELECT
              s.song_id AS id,
              s.title    AS title,
              s.path     AS path,
              ar.artist_name AS artist,
              al.title   AS album
            FROM songs s
            JOIN artist ar ON s.artist_id = ar.artist_id
            JOIN Album  al ON s.album_id   = al.album_id
            WHERE s.song_id = ?
        """, (first_id,)).fetchone()

        if song:
            session['current_song'] = {
                'id': song['id'],
                'title': song['title'],
                'path': song['path'],
                'artist': song['artist'],
                'album': song['album']
            }

    # Recommended songs (most listened genre or fallback)
    recommended_songs = conn.execute("""
        SELECT song_id, title
        FROM songs
        WHERE genre = (
            SELECT s.genre
            FROM ListeningHistory lh
            JOIN songs s ON lh.song_id = s.song_id
            WHERE lh.user_id = ?
            GROUP BY s.genre
            ORDER BY COUNT(*) DESC
            LIMIT 1
        )
        ORDER BY RANDOM()
        LIMIT 10;
    """, (user_id,)).fetchall()

    if not recommended_songs:
        recommended_songs = conn.execute("""
            SELECT song_id, title
            FROM songs
            ORDER BY RANDOM()
            LIMIT 10;
        """).fetchall()

    # Kullanıcıya ait playlistler
    user_playlists = conn.execute("""
        SELECT playlist_id, playlist_name AS name
        FROM UserPlaylist
        WHERE creator_id = ?
    """, (user_id,)).fetchall()

    # Blend playlistler
    blend_rows = conn.execute("""
        SELECT playlist_id, playlist_name AS name
        FROM BlendPlaylist
        WHERE user1_id = ? OR user2_id = ?
    """, (user_id, user_id)).fetchall()

    user_playlists.extend(blend_rows)

    conn.close()

    return render_template(
        "user_home.html",
        recent_songs=recent_songs,
        recommended_songs=recommended_songs,
        user_playlists=user_playlists
    )


@app.route('/api/playlists/<int:playlist_id>/songs/<int:song_id>', methods=['DELETE'])
def remove_song_from_playlist(playlist_id, song_id):
    remove_song_from_user_playlist(playlist_id, song_id)
    
    return ''

@app.route('/api/playlists/<int:playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    user_id = session.get('user_id')
    delete_user_playlist(playlist_id)
    blend_methods.delete_blend(playlist_id)
    return render_template('user_home.html')


@app.route('/play/<int:song_id>')
def play_song(song_id):
    """
    Fetches song by ID, joins with artist and Album tables to retrieve
    artist name and album title, stores details in session, and
    records listening history.
    """
    conn = get_db_connection()
    # Join songs -> artist -> Album to fetch metadata
    song = conn.execute(
        """
        SELECT
            s.title            AS title,
            s.path             AS path,
            ar.artist_name     AS artist,
            al.title           AS album
        FROM songs s
        JOIN artist ar ON s.artist_id = ar.artist_id
        JOIN Album  al ON s.album_id   = al.album_id
        WHERE s.song_id = ?
        """,
        (song_id,)
    ).fetchone()
    conn.close()

    if song:
        # Store in session for front-end expand button
        session['current_song'] = {
            'id':     song_id,
            'title':  song['title'],
            'path':   song['path'],
            'artist': song['artist'] or '',
            'album':  song['album']  or ''
        }
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO ListeningHistory (user_id, song_id, time_stamp)"
            " VALUES (?, ?, datetime('now'))",
            (session.get('user_id'), song_id)
        )
        conn.commit()
        conn.close()

    return redirect(url_for('user_home', autoplay=1))


@app.route("/add_song", methods=["GET", "POST"])
def add_song():
    """
    Register a new song:
    - form fields: "title", "artist", and file upload "audio_file"
    - we compute fingerprints & insert into DB
    """
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        artist_name = request.form.get("artist", "").strip()
        genre = request.form.get("genre", "").strip() or "Unknown"
        album_title = request.form.get("album", "").strip()
        file = request.files.get("audio_file", None)

        if not title or not artist_name or not file or file.filename == "":
            flash("All required fields must be filled.", "warning")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Only WAV and MP3 files are allowed.", "warning")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        saved_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(saved_path)

        registerSong(saved_path, title, artist_name, album_title, genre)

        os.remove(saved_path)
        return redirect(url_for("admin_home"))

    return render_template("add_song.html")


@app.route('/playlists/create', methods=['GET'])
def show_create_playlist():
    # Simply render the Create Playlist form
    return render_template('create_playlist.html')


@app.route('/playlists', methods=['POST'])
def create_playlist():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    song_ids = data.get('song_ids', [])
    if not name:
        return jsonify({'error': 'Playlist name is required.'}), 400
    if not isinstance(song_ids, list):
        return jsonify({'error': 'song_ids must be a list.'}), 400
    # Yeni playlist oluştur
    playlist_id = create_user_playlist(name, session.get('user_id'))
    # Şarkıları ekle
    for sid in song_ids:
        add_song_to_user_playlist(playlist_id, sid)

    return jsonify({'success': True, 'playlist_id': playlist_id}), 201

@app.route('/api/search_songs')
def api_search_songs():
    keyword = request.args.get('q', '').strip()
    genre   = request.args.get('genre')

    conn = get_db_connection()
    sql = """
    SELECT
        s.song_id,
        s.title,
        ar.artist_name AS artist,
        al.title       AS album,
        s.genre
    FROM songs s
    LEFT JOIN artist ar ON s.artist_id = ar.artist_id
    LEFT JOIN Album  al ON s.album_id   = al.album_id
    WHERE s.title LIKE ?
    OR ar.artist_name LIKE ?
    OR al.title LIKE ?
    OR s.genre LIKE ?
    """
    params = [f"%{keyword}%"] * 4
    if genre:
        sql += " AND s.genre = ?"
        params.append(genre)

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    results = [dict(r) for r in rows]
    return jsonify(results)

@app.route('/api/playlists/<int:playlist_id>/songs')
def api_get_playlist_songs(playlist_id):
    songs = list_songs_in_user_playlist(playlist_id)
    blend_songs = blend_methods.get_blend_songs(playlist_id)
    songs.extend(blend_songs)
    return jsonify(songs)

@app.route("/search_song", methods=["GET", "POST"])
def search_song():
    if request.method == "POST":
        file = request.files.get("query_clip")

        if file is None or file.filename == "":
            flash("Please upload a .wav or .mp3 file.", "warning")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Only WAV and MP3 files are allowed.", "warning")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        saved_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(saved_path)

        conn = get_db_connection()
        c = conn.cursor()
        song_id, offset = match_query_clip(saved_path, c)
        conn.close()
        if os.path.exists(saved_path):
            os.remove(saved_path)

        if song_id is not None:
            conn = get_db_connection()
            song = conn.execute("""
                SELECT s.song_id AS id, s.title, ar.artist_name AS artist
                FROM songs s
                JOIN artist ar ON s.artist_id = ar.artist_id
                WHERE s.song_id = ?
            """, (song_id,)).fetchone()
            conn.close()

            session['popup_song'] = {
                'id': song['id'],
                'title': song['title'],
                'artist': song['artist']
            }
        else:
            session['search_result'] = 'not_found'

        return redirect(url_for("search_song"))

    return render_template("search_song.html")

@app.route("/user_search_song", methods=["GET", "POST"])
def user_search_song():
    if request.method == "POST":
        file = request.files.get("query_clip")

        if file is None or file.filename == "":
            flash("Lütfen bir .wav veya .mp3 dosyası yükleyin.", "warning")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash(".wav veya .mp3 formatı destekleniyor.", "warning")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        saved_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(saved_path)

        conn = get_db_connection()
        c = conn.cursor()
        song_id, offset = match_query_clip(saved_path, c)
        conn.close()

        if os.path.exists(saved_path):  # ← HATA ALMAMAK İÇİN BU BLOK
            os.remove(saved_path)


        if song_id is not None:
            conn = get_db_connection()
            song = conn.execute("""
                SELECT s.song_id AS id, s.title, ar.artist_name AS artist
                FROM songs s
                JOIN artist ar ON s.artist_id = ar.artist_id
                WHERE s.song_id = ?
            """, (song_id,)).fetchone()
            conn.close()

            session['popup_song'] = {
                'id': song['id'],
                'title': song['title'],
                'artist': song['artist']
            }
        else:
            session['search_result'] = 'not_found'

        return redirect(url_for("user_search_song"))

    return render_template("shazothief_user.html")


@app.route('/api/like/<int:song_id>', methods=['POST'])
def like_song(song_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO LikedSongs (user_id, song_id) VALUES (?, ?)
        """, (user_id, song_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Already liked'}), 409  # 409 Conflict
    conn.close()
    return jsonify({'success': True}), 200

@app.route('/api/liked_songs')
def api_liked_songs():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify([]), 200

    conn = get_db_connection()
    rows = conn.execute("""
        SELECT
            s.song_id   AS song_id,
            s.title     AS title,
            ar.artist_name AS artist
        FROM LikedSongs ls
        JOIN songs s ON ls.song_id = s.song_id
        LEFT JOIN artist ar ON s.artist_id = ar.artist_id
        WHERE ls.user_id = ?
    """, (user_id,)).fetchall()
    conn.close()

    liked = [dict(r) for r in rows]
    return jsonify(liked), 200
@app.route('/api/like/<int:song_id>', methods=['DELETE'])
def unlike_song(song_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_db_connection()
    # beğeniyi sil
    conn.execute(
        "DELETE FROM LikedSongs WHERE user_id = ? AND song_id = ?",
        (user_id, song_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 200

@app.route("/blend")
def blend_users():
    conn = get_db_connection()
    user_id = session.get('user_id')
    users = conn.execute("""SELECT user_id, username
                            FROM   users u
                            WHERE  u.is_admin = 0
                            AND  u.user_id <> ?
                            AND NOT EXISTS (
                                    SELECT 1
                                    FROM   BlendPlaylist bp
                                    WHERE (bp.user1_id = u.user_id AND bp.user2_id = ?)
                                    OR (bp.user2_id = u.user_id AND bp.user1_id = ?)
                                ); 
                         """, (user_id, user_id, user_id)).fetchall()
    conn.close()
    return render_template("blend.html", users=users)

@app.route('/api/user_engaged_songs')
def api_user_engaged_songs():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify([])

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT song_id, title, artist_name
        FROM (
            SELECT 
                s.song_id,
                s.title,
                ar.artist_name,
                lh.time_stamp
            FROM ListeningHistory lh
            JOIN songs s ON lh.song_id = s.song_id
            LEFT JOIN artist ar ON s.artist_id = ar.artist_id
            WHERE lh.user_id = ?

            UNION

            SELECT 
                s.song_id,
                s.title,
                ar.artist_name,
                datetime('now') AS time_stamp
            FROM LikedSongs ls
            JOIN songs s ON ls.song_id = s.song_id
            LEFT JOIN artist ar ON s.artist_id = ar.artist_id
            WHERE ls.user_id = ?
        )
        GROUP BY song_id
        ORDER BY MAX(time_stamp) DESC
        LIMIT 3;
    """, (user_id, user_id))

    result = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(result)



@app.route("/api/blend/<int:other_user_id>", methods=["POST"])
def api_create_blend(other_user_id):
    user_id = session.get("user_id")
    if not user_id:
        return "Unauthorized", 401
    # your helper does all the checks
    blend_methods.create_blend(user_id, other_user_id)
    return redirect(url_for("user_home"))

@app.route('/shazothief')
def shazothief_user_page():
    return render_template("shazothief_user.html")


# -----------------------------------------------------------------------------
# ERROR HANDLERS (optional)
# -----------------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404



# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
