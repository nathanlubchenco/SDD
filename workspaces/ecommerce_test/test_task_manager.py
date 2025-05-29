import pytest
from task_manager import OrderManager, InventoryManager, PaymentProcessor, EmailService, UserManager, AuditLog, InventoryError

@pytest.fixture
def order_manager():
    return OrderManager()

@pytest.fixture
def inventory_manager():
    return InventoryManager()

@pytest.fixture
def payment_processor():
    return PaymentProcessor()

@pytest.fixture
def email_service():
    return EmailService()

@pytest.fixture
def user_manager():
    return UserManager()

@pytest.fixture
def audit_log():
    return AuditLog()

def test_process_valid_order(order_manager, inventory_manager, payment_processor, email_service):
    # Setup: Customer has items in cart with total value $150
    cart = {'item1': 2, 'item2': 3}  # Example items
    inventory_manager.set_stock('item1', 10)
    inventory_manager.set_stock('item2', 10)
    payment_info = {'card_number': '1234567890123456', 'expiry': '12/25', 'cvv': '123'}

    # Action: Customer submits order with valid payment information
    order_id = order_manager.submit_order(cart, payment_info)

    # Assertions
    assert order_id is not None, "Order ID should be generated"
    assert payment_processor.is_payment_successful(order_id), "Payment should be processed successfully"
    assert inventory_manager.get_stock('item1') == 8, "Inventory for item1 should be updated"
    assert inventory_manager.get_stock('item2') == 7, "Inventory for item2 should be updated"
    assert email_service.is_confirmation_sent(order_id), "Order confirmation email should be sent"
    assert order_manager.get_order_status(order_id) == "processing", "Order status should be 'processing'"

def test_handle_insufficient_inventory(order_manager, inventory_manager, payment_processor):
    # Setup: Customer attempts to order 10 units of product with only 5 in stock
    cart = {'item1': 10}
    inventory_manager.set_stock('item1', 5)

    # Action: Customer submits the order
    with pytest.raises(InventoryError) as excinfo:
        order_manager.submit_order(cart, {})

    # Assertions
    assert "insufficient stock" in str(excinfo.value), "Error message should indicate insufficient stock"
    assert not payment_processor.is_any_payment_processed(), "No payment should be processed"
    assert order_manager.get_cart() == cart, "Cart should remain unchanged"

def test_process_order_with_authentication(order_manager, user_manager, audit_log):
    # Setup: Authenticated user with valid session token
    user_id = 'user123'
    session_token = 'valid_token'
    user_manager.authenticate(user_id, session_token)
    cart = {'item1': 1, 'item2': 2}

    # Action: User places order through API
    order_id = order_manager.submit_order_with_auth(cart, session_token)

    # Assertions
    assert user_manager.is_user_verified(user_id, session_token), "User identity should be verified"
    assert order_manager.get_order_user(order_id) == user_id, "Order should be associated with user account"
    assert user_manager.is_order_in_history(user_id, order_id), "Order history should be updated"
    assert audit_log.is_transaction_recorded(order_id), "Audit log should record the transaction"