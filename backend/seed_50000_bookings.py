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

def generate_50k_bookings(count: int = 50000):
    print(f"[START] Seeding {count} booking records for large-scale analytics performance testing...")
    start_time = time.time()

    db = get_db()
    cur = db.cursor()

    # Get active showtimes
    cur.execute("SELECT id, price FROM showtimes")
    showtime_rows = cur.fetchall()
    if not showtime_rows:
        print("[ERROR] No showtimes found. Run seed_5000_movies.py first.")
        return

    st_ids = [r[0] for r in showtime_rows]
    st_prices = {r[0]: r[1] for r in showtime_rows}

    # Get active users
    cur.execute("SELECT id FROM users LIMIT 10")
    u_rows = cur.fetchall()
    u_ids = [r[0] for r in u_rows] if u_rows else [1]

    start_date = datetime.datetime.now() - datetime.timedelta(days=90)

    bookings_batch = []
    payments_batch = []

    statuses = ["confirmed", "confirmed", "confirmed", "confirmed", "cancelled"] # 20% cancellation rate simulation

    for i in range(1, count + 1):
        st_id = random.choice(st_ids)
        price = st_prices[st_id]
        num_seats = random.randint(1, 4)
        total_amount = price * num_seats
        uid = random.choice(u_ids)
        status = random.choice(statuses)

        # Generate timestamp over the past 90 days
        random_minutes = random.randint(0, 90 * 24 * 60)
        created_at = (start_date + datetime.timedelta(minutes=random_minutes)).strftime("%Y-%m-%d %H:%M:%S")

        payment_id = f"pay_50k_{i}_{random.randint(100, 999)}"
        order_id = f"order_50k_{i}_{random.randint(100, 999)}"
        ikey = f"ik_50k_{i}_{random.randint(1000, 9999)}"
        seats_json = f'["A{random.randint(1, 10)}", "B{random.randint(1, 10)}"]'

        bookings_batch.append((uid, st_id, seats_json, total_amount, payment_id, ikey, status, created_at))
        payments_batch.append((uid, payment_id, order_id, ikey, total_amount, "INR", "UPI", "captured" if status == "confirmed" else "failed", created_at))

    # Bulk insert bookings
    cur.executemany(
        "INSERT INTO movie_bookings (user_id, showtime_id, seats_json, total_amount, payment_id, idempotency_key, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        bookings_batch
    )

    # Bulk insert payments
    cur.executemany(
        "INSERT INTO payments (user_id, payment_id, order_id, idempotency_key, amount, currency, payment_method, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        payments_batch
    )

    db.commit()
    cur.close()
    db.close()

    elapsed = round(time.time() - start_time, 2)
    print(f"[SUCCESS] Seeded {count} bookings into database in {elapsed} seconds!")

if __name__ == "__main__":
    generate_50k_bookings(50000)
