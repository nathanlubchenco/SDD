from dataclasses import dataclass, field
from typing import List, Dict, Any
from pydantic import BaseModel, ValidationError, validator
import uuid
import logging
import time
import asyncio
import threading
from functools import wraps
from datetime import datetime
import jwt

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom Exceptions
class InventoryError(Exception):
    pass

class AuthenticationError(Exception):
    pass

class PaymentError(Exception):
    pass

# Data Models
@dataclass
class User:
    user_id: str
    email: str
    role: str
    session_token: str

@dataclass
class Order:
    order_id: str
    user_id: str
    items: List[Dict[str, Any]]
    total_value: float
    status: str = "pending"

# Pydantic Models for Validation
class OrderRequestModel(BaseModel):
    user_id: str
    items: List[Dict[str, Any]]
    total_value: float

    @validator('total_value')
    def check_total_value(cls, v):
        if v <= 0:
            raise ValueError('Total value must be greater than zero')
        return v

# Decorators
def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result
    return wrapper

def jwt_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        user = kwargs.get('user')
        if not user or not verify_jwt(user.session_token):
            raise AuthenticationError("Invalid or missing JWT token")
        return await func(*args, **kwargs)
    return wrapper

def verify_jwt(token: str) -> bool:
    try:
        # Simulate JWT verification
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

# Manager Class
class OrderManager:
    def __init__(self):
        self.orders = {}
        self.inventory = {"product_1": 5}
        self.lock = threading.Lock()

    @timing_decorator
    @jwt_required
    async def process_order(self, order_data: Dict[str, Any], user: User):
        try:
            order_request = OrderRequestModel(**order_data)
            self._check_inventory(order_request.items)
            order_id = str(uuid.uuid4())
            order = Order(order_id=order_id, user_id=user.user_id, items=order_request.items, total_value=order_request.total_value)
            self._process_payment(order)
            self._update_inventory(order.items)
            self._send_confirmation_email(user.email, order)
            order.status = "processing"
            self.orders[order_id] = order
            self._log_audit(user, order)
            return order
        except (ValidationError, InventoryError, PaymentError) as e:
            logger.error(f"Order processing failed: {str(e)}")
            raise

    def _check_inventory(self, items: List[Dict[str, Any]]):
        with self.lock:
            for item in items:
                if self.inventory.get(item['product_id'], 0) < item['quantity']:
                    raise InventoryError(f"Insufficient stock for product {item['product_id']}")

    def _process_payment(self, order: Order):
        # Simulate payment processing
        if order.total_value > 0:
            time.sleep(1)  # Simulate delay
        else:
            raise PaymentError("Payment processing failed")

    def _update_inventory(self, items: List[Dict[str, Any]]):
        with self.lock:
            for item in items:
                self.inventory[item['product_id']] -= item['quantity']

    def _send_confirmation_email(self, email: str, order: Order):
        logger.info(f"Sending confirmation email to {email} for order {order.order_id}")

    def _log_audit(self, user: User, order: Order):
        logger.info(f"Audit log: User {user.user_id} placed order {order.order_id}")

# Example Usage
async def main():
    user = User(user_id="123", email="user@example.com", role="customer", session_token="valid_jwt_token")
    order_data = {
        "user_id": user.user_id,
        "items": [{"product_id": "product_1", "quantity": 2}],
        "total_value": 150.0
    }
    order_manager = OrderManager()
    try:
        order = await order_manager.process_order(order_data, user=user)
        logger.info(f"Order processed successfully: {order}")
    except Exception as e:
        logger.error(f"Failed to process order: {str(e)}")

# Run the example