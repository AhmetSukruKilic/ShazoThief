import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "shazothief.db")


def return_user_name(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        print(f"User with ID {user_id} does not exist.")
        return None
    
def return_user_id(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        print(f"User {username} does not exist.")
        return None

def signAdmin(username, password):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            'INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
            (username, password, 1)  # 1 for admin
        )
        conn.commit()
        print(f'Admin registration is successful: {username}')
    except sqlite3.IntegrityError:
        print('This username is already taken')
    finally:
        conn.close()

def signUser(username, password, email="", phone_number=""):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            'INSERT INTO users (username, password, email, phone_number, is_admin) VALUES (?, ?, ?, ?, ?)',
            (username, password, email, phone_number, 0)
        )
        conn.commit()
        print('Sign up is successful. You may now login.')
    except sqlite3.IntegrityError:
        print('This user already exists.')
    finally:
        conn.close()

if __name__ == '__main__':
    signAdmin("b", "123")
