import sys
import os
import random
import time
import datetime

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.db.connection import get_db

def generate_large_catalog(count: int = 5000):
    print(f"[START] Seeding {count} movies into database catalog for large-scale performance testing...")
    start_time = time.time()

    db = get_db()
    cur = db.cursor()

    # Get existing genres
    cur.execute("SELECT id, name FROM genres")
    genre_rows = cur.fetchall()
    if not genre_rows:
        default_genres = ["Action", "Comedy", "Drama", "Sci-Fi", "Thriller", "Romance", "Horror", "Animation"]
        for gname in default_genres:
            cur.execute("INSERT INTO genres (name) VALUES (%s)", (gname,))
        db.commit()
        cur.execute("SELECT id, name FROM genres")
        genre_rows = cur.fetchall()

    genre_ids = [r[0] for r in genre_rows]
    languages = ["English", "Hindi", "Telugu", "Tamil", "Spanish", "French", "Japanese", "Korean"]

    adjectives = ["Cosmic", "Dark", "Infinite", "Desi", "Secret", "Silent", "Eternal", "Shadow", "Brave", "Lost", "Quantum", "Cyber"]
    nouns = ["Odyssey", "Warriors", "Knight", "Romance", "Resurgence", "Manor", "Echoes", "Realm", "Horizon", "Ascent", "Legacy", "Protocol"]

    posters = [
        "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=500",
        "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=500",
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500",
        "https://images.unsplash.com/photo-1518676590629-3dcbd9c5a5c9?w=500",
        "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500"
    ]

    start_date = datetime.date(2018, 1, 1)

    movies_batch = []
    movie_genres_batch = []

    cur.execute("SELECT COALESCE(MAX(id), 0) FROM movies")
    current_max_id = cur.fetchone()[0]

    for i in range(1, count + 1):
        mid = current_max_id + i
        title = f"{random.choice(adjectives)} {random.choice(nouns)} #{mid}"
        desc = f"An epic cinematic story of {title.lower()} featuring thrilling adventure and drama."
        dur = random.randint(90, 180)
        rdate = (start_date + datetime.timedelta(days=random.randint(0, 2500))).strftime("%Y-%m-%d")
        rating = round(random.uniform(5.5, 9.8), 1)
        popularity = random.randint(50, 1000)
        lang = random.choice(languages)
        poster = random.choice(posters)
        trailer = "https://www.youtube.com/watch?v=YoHD9XEInc0"

        movies_batch.append((title, desc, dur, rdate, rating, popularity, lang, poster, trailer))

        # Assign 1 to 3 random genres per movie
        assigned_genres = random.sample(genre_ids, random.randint(1, min(3, len(genre_ids))))
        for gid in assigned_genres:
            movie_genres_batch.append((mid, gid))

    # Bulk Insert Movies
    cur.executemany(
        "INSERT INTO movies (title, description, duration_minutes, release_date, rating, popularity, language, poster_url, trailer_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        movies_batch
    )

    # Bulk Insert Movie-Genre mappings
    cur.executemany(
        "INSERT INTO movie_genres (movie_id, genre_id) VALUES (%s, %s)",
        movie_genres_batch
    )

    db.commit()
    cur.close()
    db.close()

    elapsed = round(time.time() - start_time, 2)
    print(f"[SUCCESS] Seeded {count} movies into database in {elapsed} seconds!")

if __name__ == "__main__":
    generate_large_catalog(5000)
