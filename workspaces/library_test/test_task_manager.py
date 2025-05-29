import pytest
from task_manager import Library, User, Book, Reservation, LendingRecord, InterLibraryLoan, Notification

@pytest.fixture
def library_setup():
    library = Library()
    library.add_book(Book(title="Python Programming", copies=3))
    library.add_book(Book(title="Data Structures", copies=1))
    library.add_book(Book(title="Algorithms", copies=1))
    library.register_user(User(username="john_doe"))
    library.register_user(User(username="jane_smith"))
    library.register_user(User(username="bob_wilson"))
    library.register_user(User(username="alex_jones"))
    return library

def test_reserve_available_book(library_setup):
    library = library_setup
    user = library.get_user("john_doe")
    book = library.get_book("Python Programming")
    
    reservation = library.reserve_book(user, book)
    
    assert reservation is not None, "Reservation should be created"
    assert reservation.id is not None, "Reservation should have a unique ID"
    assert book.copies == 2, "Available copies should decrease from 3 to 2"
    assert user.has_reservation_confirmation(reservation), "User should receive reservation confirmation"
    assert reservation.expires_in_days == 7, "Reservation should expire in 7 days if not collected"

def test_lend_reserved_book(library_setup):
    library = library_setup
    user = library.get_user("jane_smith")
    book = library.get_book("Data Structures")
    reservation = library.reserve_book(user, book)
    
    lending_record = library.lend_reserved_book(user, reservation)
    
    assert reservation.status == "fulfilled", "Reservation status should change to 'fulfilled'"
    assert book.status == "borrowed", "Book status should change to 'borrowed'"
    assert lending_record is not None, "Lending record should be created"
    assert lending_record.return_period_days == 14, "Lending record should have a 14-day return period"
    assert lending_record.late_fee_policy_activated, "Late fee policy should be activated for due date"

def test_handle_book_return_with_late_fee(library_setup):
    library = library_setup
    user = library.get_user("bob_wilson")
    book = library.get_book("Algorithms")
    lending_record = library.lend_book(user, book)
    lending_record.due_date_passed_by_days = 5
    
    library.process_return(user, book)
    
    assert book.status == "available", "Book status should change to 'available'"
    assert user.late_fee == 2.50, "Late fee of $2.50 should be calculated"
    assert user.account_balance == -2.50, "User account should be charged the late fee"
    assert book.marked_for_inspection, "Book should be marked for inspection before re-shelving"

def test_process_inter_library_loan(library_setup):
    library = library_setup
    user = library.get_user("john_doe")
    book_title = "Advanced Calculus"
    
    inter_library_loan = library.request_inter_library_loan(user, book_title)
    
    assert inter_library_loan.request_sent, "Request should be sent to partner libraries"
    assert 3 <= inter_library_loan.estimated_delivery_days <= 5, "Estimated delivery time should be 3-5 business days"
    assert user.notified_on_arrival, "User should be notified when book arrives"
    assert inter_library_loan.special_loan_terms == (21, False), "Special loan terms should apply (21-day period, no renewal)"

def test_handle_user_suspension(library_setup):
    library = library_setup
    user = library.get_user("alex_jones")
    user.late_fees = 25
    user.days_overdue = 30
    
    library.process_monthly_account_review(user)
    
    assert user.status == "suspended", "User account status should change to 'suspended'"
    assert not user.active_reservations, "All active reservations should be cancelled"
    assert not user.can_make_new_reservations, "User should not be able to make new reservations or loans"
    assert user.received_notification, "Notification should be sent with payment instructions"