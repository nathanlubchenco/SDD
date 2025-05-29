import pytest
from ecommerce_module import OrderManager, InventoryError, PaymentProcessor, EmailService, UserManager, AuditLog

# Fixtures for common setup
@pytest.fixture
def order_manager():
    return OrderManager()

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

# Test for processing a valid order
def test_process_valid_order(order_manager, payment_processor, email_service):
    # Setup: Customer has items in cart with total value $150
    cart = {'item1': 2, 'item2': 3}  # Example cart items
    order_manager.add_to_cart(cart)
    
    # Action: Customer submits order with valid payment information
    order_id = order_manager.submit_order(payment_info={'card_number': '1234-5678-9012-3456'})
    
    # Verify: Order is created with unique order ID
    assert order_id is not None, "Order ID should not be None"
    assert isinstance(order_id, str), "Order ID should be a string"
    
    # Verify: Payment is processed successfully
    assert payment_processor.is_payment_successful(order_id), "Payment should be processed successfully"
    
    # Verify: Inventory is updated for all items
    for item in cart:
        assert order_manager.inventory[item] < cart[item], f"Inventory for {item} should be reduced"
    
    # Verify: Order confirmation email is sent
    assert email_service.is_email_sent(order_id), "Order confirmation email should be sent"
    
    # Verify: Order status is set to "processing"
    assert order_manager.get_order_status(order_id) == "processing", "Order status should be 'processing'"

# Test for handling insufficient inventory
def test_handle_insufficient_inventory(order_manager):
    # Setup: Customer attempts to order 10 units of product with only 5 in stock
    order_manager.inventory['product'] = 5
    cart = {'product': 10}
    order_manager.add_to_cart(cart)
    
    # Action: Customer submits the order
    with pytest.raises(InventoryError) as excinfo:
        order_manager.submit_order(payment_info={'card_number': '1234-5678-9012-3456'})
    
    # Verify: Order creation fails with InventoryError
    assert "insufficient stock" in str(excinfo.value), "Error message should indicate insufficient stock"
    
    # Verify: No payment is processed
    assert not order_manager.is_payment_attempted(), "No payment should be processed"
    
    # Verify: Cart remains unchanged
    assert order_manager.get_cart() == cart, "Cart should remain unchanged"

# Test for processing order with authentication
def test_process_order_with_authentication(order_manager, user_manager, audit_log):
    # Setup: Authenticated user with valid session token
    user = user_manager.authenticate_user('user123', 'valid_token')
    order_manager.set_user(user)
    
    # Action: User places order through API
    order_id = order_manager.submit_order(payment_info={'card_number': '1234-5678-9012-3456'})
    
    # Verify: User identity is verified
    assert user_manager.is_user_authenticated(user), "User identity should be verified"
    
    # Verify: Order is associated with user account
    assert order_manager.get_order_user(order_id) == user, "Order should be associated with user account"
    
    # Verify: Order history is updated
    assert order_id in user_manager.get_order_history(user), "Order history should be updated"
    
    # Verify: Audit log records the transaction
    assert audit_log.is_transaction_logged(order_id), "Audit log should record the transaction"