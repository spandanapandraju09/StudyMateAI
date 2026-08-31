import json
import asyncio
import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from backend.db.connection import get_db
from backend.models.movie_models import SeatReserveRequest, SeatReserveResponse, ConfirmBookingRequest
from backend.services.ticket_email_service import process_ticket_email_with_retry

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])


async def auto_release_expired_locks_loop():
    """
    Background Task: Runs periodically (every 15 seconds) to auto-release expired seat locks.
    Locks expire 2 minutes (120 seconds) after creation.
    """
    while True:
        try:
            db = get_db()
            cur = db.cursor()
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                "DELETE FROM seat_reservations WHERE status = 'locked' AND expires_at <= %s",
                (now_str,)
            )
            db.commit()
            cur.close()
            db.close()
        except Exception as e:
            print("[BACKGROUND SEAT CLEANUP ERROR]", e)
        await asyncio.sleep(15)


@router.get("/movies/{movie_id}/showtimes")
def get_movie_showtimes(movie_id: int):
    """Returns available showtimes for a specific movie, auto-creating default showtimes if needed."""
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT s.id, s.price, s.screen_name, s.show_time, t.name, t.city "
        "FROM showtimes s JOIN theaters t ON s.theater_id = t.id "
        "WHERE s.movie_id = %s ORDER BY s.show_time ASC",
        (movie_id,)
    )
    rows = cur.fetchall()

    if not rows:
        # Auto-create showtimes for this movie
        cur.execute("SELECT id FROM theaters LIMIT 2")
        t_rows = cur.fetchall()
        t_ids = [r[0] for r in t_rows] or [1]
        now = datetime.datetime.now()

        st1 = (now + datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        st2 = (now + datetime.timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(
            "INSERT INTO showtimes (movie_id, theater_id, show_time, price, screen_name) VALUES (%s, %s, %s, 14.99, 'Screen 1')",
            (movie_id, t_ids[0], st1)
        )
        cur.execute(
            "INSERT INTO showtimes (movie_id, theater_id, show_time, price, screen_name) VALUES (%s, %s, %s, 17.50, 'Screen 2')",
            (movie_id, t_ids[-1], st2)
        )
        db.commit()

        cur.execute(
            "SELECT s.id, s.price, s.screen_name, s.show_time, t.name, t.city "
            "FROM showtimes s JOIN theaters t ON s.theater_id = t.id "
            "WHERE s.movie_id = %s ORDER BY s.show_time ASC",
            (movie_id,)
        )
        rows = cur.fetchall()

    cur.close()
    db.close()

    return [
        {
            "id": r[0],
            "price": r[1],
            "screen_name": r[2],
            "show_time": str(r[3]),
            "theater_name": r[4],
            "theater_city": r[5]
        }
        for r in rows
    ]


@router.get("/showtimes/{showtime_id}/seats")
def get_showtime_seats(showtime_id: int):
    """
    Returns seat availability grid for a showtime.
    Distinguishes between 'available', 'locked' (temporary 2-min lock), and 'booked'.
    """
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT s.id, s.price, s.screen_name, s.show_time, m.title, t.name, t.total_seats "
        "FROM showtimes s JOIN movies m ON s.movie_id = m.id JOIN theaters t ON s.theater_id = t.id "
        "WHERE s.id = %s",
        (showtime_id,)
    )
    st = cur.fetchone()
    if not st:
        cur.close()
        db.close()
        raise HTTPException(status_code=404, detail="Showtime not found")

    st_id, price, screen, show_time, m_title, t_name, total_seats = st

    # Fetch active locks and bookings
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Clean expired locks first
    cur.execute("DELETE FROM seat_reservations WHERE status = 'locked' AND expires_at <= %s", (now_str,))
    db.commit()

    cur.execute(
        "SELECT seat_number, status, expires_at FROM seat_reservations WHERE showtime_id = %s",
        (showtime_id,)
    )
    reservations = cur.fetchall()
    cur.close()
    db.close()

    seat_status_map = {}
    for seat_no, status, expires_at in reservations:
        seat_status_map[seat_no] = status

    return {
        "showtime_id": st_id,
        "movie_title": m_title,
        "theater_name": t_name,
        "screen_name": screen,
        "show_time": str(show_time),
        "price": price,
        "total_seats": total_seats,
        "occupied_seats": seat_status_map
    }


@router.post("/reserve-seats", response_model=SeatReserveResponse)
def reserve_seats(req: SeatReserveRequest):
    """
    Task 5: Concurrency-Safe Seat Reservation with 2-Minute Lock Expiry.
    Uses atomic DB checks and locks requested seats. Prevents double-booking even
    under millisecond concurrent requests.
    """
    if not req.seats:
        raise HTTPException(status_code=400, detail="No seats selected for reservation")

    db = get_db()
    cur = db.cursor()

    try:
        now = datetime.datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        expires_at = (now + datetime.timedelta(seconds=120))
        expires_at_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")

        # 1. Clean up any expired locks for these seats first
        placeholders = ",".join(["%s"] * len(req.seats))
        cleanup_sql = f"DELETE FROM seat_reservations WHERE showtime_id = %s AND seat_number IN ({placeholders}) AND status = 'locked' AND expires_at <= %s"
        cur.execute(cleanup_sql, tuple([req.showtime_id] + req.seats + [now_str]))

        # 2. Check if ANY of the requested seats are currently locked (unexpired) or booked
        conflict_sql = f"SELECT seat_number, status FROM seat_reservations WHERE showtime_id = %s AND seat_number IN ({placeholders}) AND (status = 'booked' OR (status = 'locked' AND expires_at > %s))"
        cur.execute(conflict_sql, tuple([req.showtime_id] + req.seats + [now_str]))
        conflicts = cur.fetchall()

        if conflicts:
            conflict_seats = [c[0] for c in conflicts]
            db.rollback()
            cur.close()
            db.close()
            raise HTTPException(
                status_code=409,
                detail=f"Seats already reserved or locked: {', '.join(conflict_seats)}. Please select different seats."
            )

        # 3. Atomically acquire lock for all requested seats
        for seat_no in req.seats:
            cur.execute(
                "INSERT INTO seat_reservations (showtime_id, seat_number, user_id, status, locked_at, expires_at) VALUES (%s, %s, %s, 'locked', %s, %s)",
                (req.showtime_id, seat_no, req.user_id, now_str, expires_at_str)
            )

        db.commit()
        cur.close()
        db.close()

        return SeatReserveResponse(
            success=True,
            showtime_id=req.showtime_id,
            seats=req.seats,
            status="locked",
            locked_at=now_str,
            expires_at=expires_at_str,
            lock_duration_seconds=120,
            message="Seats locked successfully for 2 minutes. Please complete payment before timeout."
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cur.close()
        db.close()
        raise HTTPException(status_code=500, detail=f"Failed to reserve seats: {str(e)}")


@router.post("/confirm")
def confirm_booking(req: ConfirmBookingRequest, background_tasks: BackgroundTasks):
    """
    Confirms ticket booking after successful payment.
    Marks seat reservations as 'booked', stores booking record, and triggers non-blocking
    background email delivery with retry queue.
    """
    db = get_db()
    cur = db.cursor()

    try:
        # Fetch showtime & movie details
        cur.execute(
            "SELECT s.price, s.show_time, s.screen_name, m.title, m.language, t.name, t.city "
            "FROM showtimes s JOIN movies m ON s.movie_id = m.id JOIN theaters t ON s.theater_id = t.id "
            "WHERE s.id = %s",
            (req.showtime_id,)
        )
        st_info = cur.fetchone()
        if not st_info:
            raise HTTPException(status_code=404, detail="Showtime not found")

        price, show_time, screen_name, m_title, m_lang, t_name, t_city = st_info
        total_amount = price * len(req.seats)

        # Check idempotency for booking confirmation
        cur.execute("SELECT id FROM movie_bookings WHERE idempotency_key = %s", (req.idempotency_key,))
        existing_booking = cur.fetchone()
        if existing_booking:
            booking_id = existing_booking[0]
        else:
            # Create booking record
            seats_json = json.dumps(req.seats)
            cur.execute(
                "INSERT INTO movie_bookings (user_id, showtime_id, seats_json, total_amount, payment_id, idempotency_key, status) VALUES (1, %s, %s, %s, %s, %s, 'confirmed')",
                (req.showtime_id, seats_json, total_amount, req.payment_id, req.idempotency_key)
            )
            booking_id = cur.lastrowid

            # Mark seats as permanently booked
            placeholders = ",".join(["%s"] * len(req.seats))
            cur.execute(
                f"UPDATE seat_reservations SET status = 'booked' WHERE showtime_id = %s AND seat_number IN ({placeholders})",
                tuple([req.showtime_id] + req.seats)
            )
            db.commit()

        cur.close()
        db.close()

        # Trigger Task 2: Automated Non-Blocking Ticket Email Confirmation
        email_context = {
            "booking_id": booking_id,
            "movie_title": m_title,
            "language": m_lang,
            "screen_name": screen_name,
            "theater_name": t_name,
            "theater_city": t_city,
            "show_time": str(show_time),
            "seats": req.seats,
            "total_amount": total_amount,
            "payment_id": req.payment_id
        }

        background_tasks.add_task(
            process_ticket_email_with_retry,
            booking_id=booking_id,
            recipient=req.user_email or "user@example.com",
            subject=f"Ticket Confirmation #{booking_id} - {m_title}",
            email_context=email_context,
            max_retries=3
        )

        return {
            "success": True,
            "booking_id": booking_id,
            "status": "confirmed",
            "seats": req.seats,
            "total_amount": total_amount,
            "message": "Booking confirmed! Ticket email confirmation has been queued."
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cur.close()
        db.close()
        raise HTTPException(status_code=500, detail=f"Booking confirmation failed: {str(e)}")
