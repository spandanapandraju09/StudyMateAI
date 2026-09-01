import re
import math
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Depends
from backend.db.connection import get_db
from backend.models.movie_models import MovieListResponse, MovieSchema, TrailerResponse

router = APIRouter(prefix="/api/movies", tags=["Movies"])

YOUTUBE_REGEX = re.compile(r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})')


def extract_youtube_id(url: str) -> Optional[str]:
    """Extracts valid 11-character YouTube video ID safely preventing XSS/injection."""
    if not url:
        return None
    match = YOUTUBE_REGEX.search(url)
    if match:
        return match.group(1)
    return None


@router.get("", response_model=MovieListResponse)
def get_movies(
    genres: Optional[str] = Query(None, description="Comma-separated genre names, e.g. Action,Sci-Fi"),
    languages: Optional[str] = Query(None, description="Comma-separated languages, e.g. English,Hindi"),
    search: Optional[str] = Query(None, description="Search query in title or description"),
    sort_by: str = Query("release_date", description="Sort field: release_date, rating, popularity, title"),
    sort_order: str = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100)
):
    """
    Scalable Multi-Select Filtering with Dynamic Facet Counts & Query Optimization.
    Prevent full-table scans using composite indexes on genres and languages.
    """
    db = get_db()
    cur = db.cursor()

    genre_list = [g.strip() for g in genres.split(",")] if genres and genres.strip() else []
    lang_list = [l.strip() for l in languages.split(",")] if languages and languages.strip() else []

    # Base WHERE clauses for movies
    where_clauses = []
    params = []

    if lang_list:
        placeholders = ",".join(["%s"] * len(lang_list))
        where_clauses.append(f"m.language IN ({placeholders})")
        params.extend(lang_list)

    if search and search.strip():
        where_clauses.append("(m.title LIKE %s OR m.description LIKE %s)")
        search_param = f"%{search.strip()}%"
        params.extend([search_param, search_param])

    if genre_list:
        placeholders = ",".join(["%s"] * len(genre_list))
        where_clauses.append(
            f"m.id IN (SELECT mg.movie_id FROM movie_genres mg JOIN genres g ON mg.genre_id = g.id WHERE g.name IN ({placeholders}))"
        )
        params.extend(genre_list)

    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    # 1. Total Count Query (Indexed)
    count_sql = f"SELECT COUNT(DISTINCT m.id) FROM movies m{where_sql}"
    cur.execute(count_sql, tuple(params))
    total = cur.fetchone()[0]

    # Validate sort field to prevent SQL injection
    valid_sorts = {"release_date": "m.release_date", "rating": "m.rating", "popularity": "m.popularity", "title": "m.title"}
    sort_column = valid_sorts.get(sort_by, "m.release_date")
    direction = "DESC" if sort_order.lower() == "desc" else "ASC"

    # 2. Paginated Movies Query
    offset = (page - 1) * limit
    fetch_sql = f"""
    SELECT m.id, m.title, m.description, m.duration_minutes, m.release_date, m.rating, m.popularity, m.language, m.poster_url, m.trailer_url
    FROM movies m
    {where_sql}
    ORDER BY {sort_column} {direction}
    LIMIT %s OFFSET %s
    """
    cur.execute(fetch_sql, tuple(params + [limit, offset]))
    rows = cur.fetchall()

    movie_items: List[MovieSchema] = []
    movie_ids = [r[0] for r in rows]

    # Fetch genres for retrieved movies in single query
    movie_genres_map: Dict[int, List[str]] = {mid: [] for mid in movie_ids}
    if movie_ids:
        placeholders = ",".join(["%s"] * len(movie_ids))
        cur.execute(
            f"SELECT mg.movie_id, g.name FROM movie_genres mg JOIN genres g ON mg.genre_id = g.id WHERE mg.movie_id IN ({placeholders})",
            tuple(movie_ids)
        )
        for mid, gname in cur.fetchall():
            if mid in movie_genres_map:
                movie_genres_map[mid].append(gname)

    for r in rows:
        mid, title, desc, dur, rdate, rating, pop, lang, poster, trailer = r
        movie_items.append(
            MovieSchema(
                id=mid,
                title=title,
                description=desc,
                duration_minutes=dur,
                release_date=rdate,
                rating=rating,
                popularity=pop,
                language=lang,
                poster_url=poster,
                trailer_url=trailer,
                genres=movie_genres_map.get(mid, [])
            )
        )

    # 3. Dynamic Facet Aggregations (Counts per Genre & Language)
    # Genre facets: Filter movies by active language & search, then count genres
    facet_genre_where = []
    facet_genre_params = []
    if lang_list:
        pl = ",".join(["%s"] * len(lang_list))
        facet_genre_where.append(f"m.language IN ({pl})")
        facet_genre_params.extend(lang_list)
    if search and search.strip():
        facet_genre_where.append("(m.title LIKE %s OR m.description LIKE %s)")
        facet_genre_params.extend([f"%{search.strip()}%", f"%{search.strip()}%"])
    fg_where = (" WHERE " + " AND ".join(facet_genre_where)) if facet_genre_where else ""

    genre_facets_sql = f"""
    SELECT g.name, COUNT(DISTINCT m.id)
    FROM genres g
    JOIN movie_genres mg ON g.id = mg.genre_id
    JOIN movies m ON mg.movie_id = m.id
    {fg_where}
    GROUP BY g.name
    """
    cur.execute(genre_facets_sql, tuple(facet_genre_params))
    genre_counts = {r[0]: r[1] for r in cur.fetchall()}

    # Language facets: Filter movies by active genres & search, then count languages
    facet_lang_where = []
    facet_lang_params = []
    if genre_list:
        pl = ",".join(["%s"] * len(genre_list))
        facet_lang_where.append(f"m.id IN (SELECT mg.movie_id FROM movie_genres mg JOIN genres g ON mg.genre_id = g.id WHERE g.name IN ({pl}))")
        facet_lang_params.extend(genre_list)
    if search and search.strip():
        facet_lang_where.append("(m.title LIKE %s OR m.description LIKE %s)")
        facet_lang_params.extend([f"%{search.strip()}%", f"%{search.strip()}%"])
    fl_where = (" WHERE " + " AND ".join(facet_lang_where)) if facet_lang_where else ""

    lang_facets_sql = f"""
    SELECT m.language, COUNT(DISTINCT m.id)
    FROM movies m
    {fl_where}
    GROUP BY m.language
    """
    cur.execute(lang_facets_sql, tuple(facet_lang_params))
    lang_counts = {r[0]: r[1] for r in cur.fetchall()}

    cur.close()
    db.close()

    total_pages = math.ceil(total / limit) if total > 0 else 1

    return MovieListResponse(
        items=movie_items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        facet_counts={
            "genres": genre_counts,
            "languages": lang_counts
        }
    )


@router.get("/{movie_id}", response_model=MovieSchema)
def get_movie_detail(movie_id: int):
    """Returns detailed information for a specific movie including genres and trailer URL."""
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT id, title, description, duration_minutes, release_date, rating, popularity, language, poster_url, trailer_url FROM movies WHERE id = %s",
        (movie_id,)
    )
    row = cur.fetchone()
    if not row:
        cur.close()
        db.close()
        raise HTTPException(status_code=404, detail="Movie not found")

    mid, title, desc, dur, rdate, rating, pop, lang, poster, trailer = row

    cur.execute(
        "SELECT g.name FROM movie_genres mg JOIN genres g ON mg.genre_id = g.id WHERE mg.movie_id = %s",
        (movie_id,)
    )
    gnames = [r[0] for r in cur.fetchall()]

    cur.close()
    db.close()

    return MovieSchema(
        id=mid,
        title=title,
        description=desc,
        duration_minutes=dur,
        release_date=rdate,
        rating=rating,
        popularity=pop,
        language=lang,
        poster_url=poster,
        trailer_url=trailer,
        genres=gnames
    )


@router.get("/{movie_id}/trailer", response_model=TrailerResponse)
def get_movie_trailer(movie_id: int):
    """
    Task 3: Secure YouTube Trailer URL Verification & Sanitized Embed ID extraction.
    Prevents XSS vulnerabilities by strictly extracting and validating 11-char YouTube ID.
    """
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, title, trailer_url, poster_url FROM movies WHERE id = %s", (movie_id,))
    row = cur.fetchone()
    cur.close()
    db.close()

    if not row:
        raise HTTPException(status_code=404, detail="Movie not found")

    mid, title, trailer_url, poster_url = row
    embed_id = extract_youtube_id(trailer_url)

    if embed_id:
        embed_url = f"https://www.youtube-nocookie.com/embed/{embed_id}?rel=0&enablejsapi=1"
        return TrailerResponse(
            movie_id=mid,
            title=title,
            original_url=trailer_url,
            embed_id=embed_id,
            embed_url=embed_url,
            is_valid=True,
            fallback_poster_url=poster_url
        )
    else:
        return TrailerResponse(
            movie_id=mid,
            title=title,
            original_url=trailer_url,
            embed_id=None,
            embed_url=None,
            is_valid=False,
            fallback_poster_url=poster_url
        )
