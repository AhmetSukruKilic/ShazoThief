# ShazoThief

A university-level project that simulates a simplified version of **Shazam** — identify songs from short audio snippets, listen to tracks, create playlists, blend them with other users, and manage content with an admin panel.

## 🎵 Overview
ShazoThief uses audio fingerprinting to convert sound snippets into unique identifiers, allowing fast and accurate song recognition from a database. Beyond recognition, it supports user playlists, collaborative blends, and admin management for the music library.

## ✨ Features
- **Audio Recognition**: Identify songs and artists from short clips.  
- **User Features**:
  - Listen to songs directly.
  - Create and manage playlists.
  - Blend playlists with other users to discover shared favorites.  
- **Admin Tools**:
  - Add new songs into the database.
  - Delete or update existing songs.  
- **Database-Backed**: Uses SQLite to store songs, playlists, users, and history.

## 🛠️ Tech Stack
- **Python** – core programming language  
- **Flask** – lightweight web framework  
- **SQLite** – relational database for persistence  
- **Audio Processing** – custom scripts for song fingerprinting & search  
- **HTML/CSS** – templates for the user interface  

    ## 📂 Project Structure
      ShazoThief/
      │
      ├── app.py # Flask entry point
      ├── load_audio.py # Handles audio loading
      ├── search_audio.py # Matching algorithm for snippets
      ├── upload_song.py # Song upload functionality
      ├── song_methods.py # Song-related DB functions
      ├── artist_methods.py # Artist-related DB functions
      ├── playlist_methods.py # Playlist management
      ├── blend_methods.py # Playlist blending logic
      ├── user_methods.py # User login/playlist management
      ├── volume_editor_methods.py # Adjusting audio volume
      │
      ├── create_tables_from_zero_deletes_data.py # Reset DB and create tables
      ├── populate_table_*.py # Populate DB with initial data
      │
      ├── templates/ # HTML pages
      ├── static/ # CSS, JS, images
      │
      ├── shazothief.db # SQLite database
      └── song.txt # Sample song metadata

## 🚀 Setup & Installation
  1. **Clone the Repository**
     git clone https://github.com/AhmetSukruKilic/ShazoThief.git
     cd ShazoThief
     
  2. **Initialize the Database**
    python create_tables_from_zero_deletes_data.py
  
    (Optional) seed with test data:
    python populate_table_user.py
    python populate_table_artist.py
    python populate_table_song.py

      
  3. **Run the Application**
    python app.py

📖 Usage
  Identify Songs: Upload/record a snippet → system matches song + artist.
  Listen to Tracks: Play songs directly from the library.
  Playlists: Create and manage personal playlists.
  Blend Playlists: Mix playlists with another user to find shared or new tracks.
  Admin Panel: Add new songs or delete outdated entries.
🔮 Future Improvements
  Real-time microphone input for recognition.
  Transition to PostgreSQL/MySQL for scalability.
  Add authentication & roles (user vs admin).
  Search and filter enhancements.
  Social sharing features for playlists.
👨‍💻 Author
  Ahmet Şükrü Kılıç
  Developed as a database-focused project with audio recognition features.
