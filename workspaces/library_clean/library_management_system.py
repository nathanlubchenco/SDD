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
    reservation_id: str
    book_title: str
    username: str
    status: str = "active"
    expiration_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))

@dataclass
class LendingRecord:
    lending_id: str
    book_title: str
    username: str
    due_date: datetime
    status: str = "borrowed"

# Manager Class
class LibraryManager:
    def __init__(self):
        self.books: Dict[str, Book] = {}
        self.users: Dict[str, User] = {}
        self.reservations: Dict[str, Reservation] = {}
        self.lending_records: Dict[str, LendingRecord] = {}

    def reserve_book(self, book_title: str, username: str) -> str:
        if username not in self.users:
            raise ReservationError("User not registered.")
        
        user = self.users[username]
        if user.active_reservations >= 5:
            raise ReservationError("User has reached maximum active reservations.")
        
        if book_title not in self.books or self.books[book_title].available_copies <= 0:
            raise ReservationError("Book not available for reservation.")
        
        book = self.books[book_title]
        reservation_id = str(uuid.uuid4())
        reservation = Reservation(reservation_id, book_title, username)
        self.reservations[reservation_id] = reservation
        book.available_copies -= 1
        user.active_reservations += 1
        return reservation_id

    def lend_reserved_book(self, reservation_id: str, username: str) -> str:
        if reservation_id not in self.reservations:
            raise LendingError("Reservation not found.")
        
        reservation = self.reservations[reservation_id]
        if reservation.username != username or reservation.status != "active":
            raise LendingError("Invalid reservation or user.")
        
        reservation.status = "fulfilled"
        lending_id = str(uuid.uuid4())
        lending_record = LendingRecord(lending_id, reservation.book_title, username, datetime.now() + timedelta(days=14))
        self.lending_records[lending_id] = lending_record
        return lending_id

    def process_return(self, book_title: str, username: str, days_late: int):
        if book_title not in self.books:
            raise ReturnError("Book not found.")
        
        book = self.books[book_title]
        book.status = "available"
        
        if days_late > 0:
            late_fee = min(days_late * 0.50, 20.0)
            user = self.users[username]
            user.late_fees += late_fee

    def process_inter_library_loan(self, book_title: str, username: str):
        # Simulate inter-library loan request
        if book_title not in self.books or self.books[book_title].available_copies <= 0:
            # Request sent to partner libraries
            estimated_delivery = "3-5 business days"
            return estimated_delivery
        else:
            raise ReservationError("Book is available in the current library.")

    def process_user_suspension(self, username: str):
        if username not in self.users:
            raise UserSuspensionError("User not found.")
        
        user = self.users[username]
        if user.late_fees >= 25:
            user.status = "suspended"
            user.active_reservations = 0
            # Cancel all active reservations
            for reservation in self.reservations.values():
                if reservation.username == username and reservation.status == "active":
                    reservation.status = "cancelled"

    # Additional methods for user registration, book addition, etc., would be implemented here

# Example usage
library_manager = LibraryManager()
library_manager.books["Python Programming"] = Book("Python Programming", 3, 3)
library_manager.users["john_doe"] = User("john_doe")

# Reserve a book
reservation_id = library_manager.reserve_book("Python Programming", "john_doe")