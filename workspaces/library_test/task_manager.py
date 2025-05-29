from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import uuid

# Custom Exceptions
class ReservationError(Exception):
    pass

class LendingError(Exception):
    pass

class ReturnError(Exception):
    pass

class UserSuspensionError(Exception):
    pass

# Data Models
@dataclass
class Book:
    title: str
    total_copies: int
    available_copies: int
    status: str = "available"

@dataclass
class User:
    username: str
    active_reservations: int = 0
    late_fees: float = 0.0
    status: str = "active"

@dataclass
class Reservation:
    book_title: str
    user: User
    reservation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "active"
    expiration_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))

@dataclass
class LendingRecord:
    book_title: str
    user: User
    due_date: datetime
    status: str = "borrowed"

# Manager Class
class LibraryManager:
    def __init__(self):
        self.books: Dict[str, Book] = {}
        self.users: Dict[str, User] = {}
        self.reservations: Dict[str, Reservation] = {}
        self.lending_records: List[LendingRecord] = []

    def reserve_book(self, username: str, book_title: str) -> str:
        if username not in self.users:
            raise ReservationError("User not registered.")
        if book_title not in self.books:
            raise ReservationError("Book not available in library.")
        
        user = self.users[username]
        book = self.books[book_title]

        if user.active_reservations >= 5:
            raise ReservationError("User has reached maximum active reservations.")
        if book.available_copies <= 0:
            raise ReservationError("No copies available for reservation.")

        reservation = Reservation(book_title=book_title, user=user)
        self.reservations[reservation.reservation_id] = reservation
        book.available_copies -= 1
        user.active_reservations += 1

        return reservation.reservation_id

    def lend_reserved_book(self, reservation_id: str, user_id: str):
        if reservation_id not in self.reservations:
            raise LendingError("Reservation not found.")
        
        reservation = self.reservations[reservation_id]
        if reservation.user.username != user_id:
            raise LendingError("User ID does not match reservation.")
        
        reservation.status = "fulfilled"
        lending_record = LendingRecord(
            book_title=reservation.book_title,
            user=reservation.user,
            due_date=datetime.now() + timedelta(days=14)
        )
        self.lending_records.append(lending_record)

    def process_return(self, book_title: str, username: str, days_late: int):
        if username not in self.users:
            raise ReturnError("User not registered.")
        if book_title not in self.books:
            raise ReturnError("Book not found in library.")

        user = self.users[username]
        book = self.books[book_title]

        book.status = "available"
        late_fee = min(days_late * 0.50, 20.0)
        user.late_fees += late_fee

    def process_inter_library_loan(self, book_title: str, username: str):
        if username not in self.users:
            raise ReservationError("User not registered.")
        
        # Simulate inter-library loan process
        estimated_delivery = "3-5 business days"
        return estimated_delivery

    def process_user_suspension(self, username: str):
        if username not in self.users:
            raise UserSuspensionError("User not registered.")
        
        user = self.users[username]
        if user.late_fees >= 25:
            user.status = "suspended"
            user.active_reservations = 0
            # Notify user with payment instructions

    # Additional methods for user registration, book addition, etc.
    def register_user(self, username: str):
        if username in self.users:
            raise ValueError("User already registered.")
        self.users[username] = User(username=username)

    def add_book(self, title: str, total_copies: int):
        if title in self.books:
            raise ValueError("Book already exists in library.")
        self.books[title] = Book(title=title, total_copies=total_copies, available_copies=total_copies)