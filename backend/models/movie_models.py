from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Task 1: Movie Filtering & Response Schemas
class MovieGenreSchema(BaseModel):
    id: int
    name: str

class MovieSchema(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    duration_minutes: int
    release_date: str
    rating: float
    popularity: int
    language: str
    poster_url: Optional[str] = None
    trailer_url: Optional[str] = None
    genres: List[str] = []

class MovieListResponse(BaseModel):
    items: List[MovieSchema]
    total: int
    page: int
    limit: int
    total_pages: int
    facet_counts: Dict[str, Any]

# Task 3: Secure YouTube Trailer Schema
class TrailerResponse(BaseModel):
    movie_id: int
    title: str
    original_url: Optional[str] = None
    embed_id: Optional[str] = None
    embed_url: Optional[str] = None
    is_valid: bool
    fallback_poster_url: Optional[str] = None

# Task 5: Seat Reservation Schemas
class SeatReserveRequest(BaseModel):
    showtime_id: int
    seats: List[str]
    user_id: Optional[int] = 1

class SeatReserveResponse(BaseModel):
    success: bool
    showtime_id: int
    seats: List[str]
    status: str
    locked_at: str
    expires_at: str
    lock_duration_seconds: int = 120
    message: str

# Task 4: Payment Schemas
class CreatePaymentOrderRequest(BaseModel):
    showtime_id: int
    seats: List[str]
    amount: float
    idempotency_key: str

class PaymentOrderResponse(BaseModel):
    order_id: str
    payment_id: str
    amount: float
    currency: str = "INR"
    idempotency_key: str
    status: str
    razorpay_key: str = "rzp_test_mock123456"

class ConfirmBookingRequest(BaseModel):
    showtime_id: int
    seats: List[str]
    payment_id: str
    order_id: str
    idempotency_key: str
    user_email: Optional[str] = "user@example.com"
    user_name: Optional[str] = "Valued Customer"

# Task 6: Admin Analytics Schemas
class AdminLoginRequest(BaseModel):
    email: str
    password: str

class RevenueData(BaseModel):
    period: str
    revenue: float
    bookings_count: int

class PopularMovieData(BaseModel):
    movie_id: int
    title: str
    total_bookings: int
    revenue: float

class TheaterOccupancyData(BaseModel):
    theater_id: int
    name: str
    city: str
    total_seats: int
    booked_seats: int
    occupancy_rate: float

class PeakHourData(BaseModel):
    hour: int
    bookings_count: int

class AnalyticsDashboardResponse(BaseModel):
    total_revenue_all_time: float
    daily_revenue: List[RevenueData]
    weekly_revenue: List[RevenueData]
    monthly_revenue: List[RevenueData]
    popular_movies: List[PopularMovieData]
    busiest_theaters: List[TheaterOccupancyData]
    peak_booking_hours: List[PeakHourData]
    cancellation_rate: float
    cached: bool = False
