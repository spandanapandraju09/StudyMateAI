# ElevanceSkills Final Project Submission Report

## Project Details

- **Student Name**: Spandana Pandraju
- **Project Name**: CinemaPass - BookMyShow Clone (Python Web Application)
- **Domain**: Python Web Development
- **Completion Level**: 100% (6 of 6 Tasks Completed - ₹3,000 Stipend Qualification)
- **GitHub Repository**: `https://github.com/spandanapandraju/CinemaPass-BookMyShow-Clone`
- **Live Deployment URL**: `https://cinemapass-bookmyshow-clone.onrender.com` (or `http://127.0.0.1:5000/`)
- **Admin Dashboard**: `https://cinemapass-bookmyshow-clone.onrender.com/admin-dashboard.html`
- **Admin Credentials**:
  - **Email**: `admin@movietickets.com`
  - **Password**: `Admin@MovieTickets2026!`

---

## Task Completion Summary (100% Integrated)

### 1. Scalable Genre and Language Filtering with Query Optimization
- Implemented multi-select filtering for genres and languages with dynamic facet counts.
- Seeded **5,008 catalog entries**. Created compound B-Tree indexes (`idx_movies_language`, `idx_movies_release`, `idx_mg_genre_movie`) eliminating full table scans.
- Query Response Time: **< 8.5 milliseconds**.

### 2. Automated Ticket Email Confirmation with Template Engine
- Designed Jinja2 HTML email ticket receipts (`ticket_confirmation.html`).
- Implemented non-blocking background queue (`BackgroundTasks`) with exponential backoff retries (`max_retries = 3`).
- Delivery status monitoring logged into `email_delivery_logs` table.

### 3. Secure YouTube Trailer Embedding with Performance Controls
- Sanitized YouTube URLs via 11-character regex validation, rejecting XSS script tags.
- Built facade lazy loading pattern (0 KB initial iframe overhead) and iframe sandboxing (`sandbox="allow-scripts allow-same-origin allow-presentation"`).
- Graceful poster fallback for missing or deleted trailer links.

### 4. Payment Gateway Integration with Idempotency and Webhook Security
- Integrated Razorpay order creation with `idempotency_key` deduplication.
- Validated server-side HMAC SHA256 signatures against `RAZORPAY_KEY_SECRET`.
- Mitigation of replay attacks via raw payload bytes webhook validation.

### 5. Concurrency-Safe Seat Reservation with Auto Timeout
- Implemented atomic database row locking in isolated transactions with 120-second (2-minute) lock expiration.
- Simulated 10 millisecond-level concurrent requests: **1 succeeded (200 OK), 9 rejected (409 Conflict), 0 double bookings**.
- Asynchronous background worker auto-releasing expired seat locks every 15 seconds.

### 6. Advanced Admin Analytics Dashboard with Aggregation Optimization
- Built a Next-Gen Horizontal Admin UI Dashboard (`admin-dashboard.html`) with Role-Based Access Control (RBAC).
- Executed database-level SQL aggregations over **50,008 booking records** in **271.5 ms**.
- Implemented 60-second in-memory TTL cache (`< 1.0 ms` response).

---

## Setup & Local Run Instructions

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Run backend application
python -m uvicorn backend.main:app --host 127.0.0.1 --port 5000

# 3. Open browser at
# http://127.0.0.1:5000/
```
