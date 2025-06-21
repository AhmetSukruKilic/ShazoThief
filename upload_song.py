import os
import sqlite3
from load_audio import registerSong

HERE        = os.path.dirname(__file__)
DB_PATH     = os.path.join(HERE, "shazothief.db")
TXT_PATH    = os.path.join(HERE, "song.txt")
SONGS_DIR   = os.path.join(HERE, "static", "Songs")


def find_file(title):
    for fname in os.listdir(SONGS_DIR):
        if fname.lower().endswith((".mp3", ".wav")) and title.lower() in fname.lower():
            return os.path.join(SONGS_DIR, fname)
    return None

def process_and_register():
    if not os.path.isfile(TXT_PATH):
        print("⚠ song.txt bulunamadı!")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    with open(TXT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            parts = [p.strip() for p in line.split(";")]
            if len(parts) != 5:
                print(f"⚠ Yanlış format: {line}")
                continue

            artist, title, genre, duration_str, album = parts
            src = find_file(title)
            if not src:
                print(f"⚠ Dosya bulunamadı: {title}")
                continue

            print(f"➕ Kayıt: {artist} – {title}")
            # 1) fingerprint + INSERT (registerSong mutlak path kullanır)
            registerSong(
                path=src,
                title=title,
                artist_name=artist,
                album_title=album,
                genre=genre
            )

            # 2) path’i relative olarak güncelle
            rel = f"Songs/{os.path.basename(src)}"
            conn.execute("""
                UPDATE songs
                   SET path = ?
                 WHERE title = ?
                   AND artist_id = (
                       SELECT artist_id FROM artist
                        WHERE artist_name = ?
                   );
            """, (rel, title, artist))
            conn.commit()
            print(f"  ✔ DB.path güncellendi: {rel}")

    conn.close()
    print("✅ Tüm şarkılar kaydedildi ve path’leri ayarlandı.")

if __name__ == "__main__":
    process_and_register()
