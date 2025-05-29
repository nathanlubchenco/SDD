from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
import asyncio
import logging
import jwt
import threading
from pydantic import BaseModel, ValidationError, validator
from functools import wraps
import time
import random

# Setup logging
logging.basicConfig(level=logging.INFO)

# Custom Exceptions
class InventoryError(Exception):
    pass

class AuthenticationError(Exception):
    pass

class PaymentError(Exception):
    pass

# JWT Token Verification Decorator
def jwt_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = kwargs.get('token')
        if not token or not verify_jwt(token):
            raise AuthenticationError("Invalid or missing JWT token")
        return func(*args, **kwargs)
    return wrapper

# Timing Decorator
def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result
    return wrapper

# Simulate JWT verification
def verify_jwt(token: str) -> bool:
    try:
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

# Data Models
@dataclass
class User:
    user_id: str
    email: str
    role: str

@dataclass
class Order:
    order_id: str
    user_id: str
    items: List[Dict[str, Any]]
    total_value: float
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)

# Pydantic Models for Validation
class OrderRequest(BaseModel):
    user_id: str
    items: List[Dict[str, Any]]
    total_value: float

    @validator('total_value')
    def check_total_value(cls, v):
        if v <= 0:
            raise ValueError('Total value must be greater than zero')
        return v

# Manager Class
class OrderManager:
    def __init__(self):
        self.orders = {}
        self.inventory = {"product_1": 5}
        self.lock = threading.Lock()

    @jwt_required
    @timing_decorator
    def process_order(self, order_data: Dict[str, Any], token: str) -> Order:
        try:
            order_request = OrderRequest(**order_data)
            self._validate_inventory(order_request.items)
            order_id = self._create_order(order_request)
            self._process_payment(order_request.total_value)
            self._update_inventory(order_request.items)
            self._send_confirmation_email(order_request.user_id)
            self._log_audit(order_id, "Order created")
            return self.orders[order_id]
        except (InventoryError, PaymentError, ValidationError) as e:
            logging.error(f"Order processing failed: {str(e)}")
            raise

    def _validate_inventory(self, items: List[Dict[str, Any]]):
        for item in items:
            if self.inventory.get(item['product_id'], 0) < item['quantity']:
                raise InventoryError(f"Insufficient stock for product {item['product_id']}")

    def _create_order(self, order_request: OrderRequest) -> str:
        order_id = f"order_{random.randint(1000, 9999)}"
        order = Order(order_id=order_id, user_id=order_request.user_id, items=order_request.items, total_value=order_request.total_value, status="processing")
        with self.lock:
            self.orders[order_id] = order
        return order_id

    def _process_payment(self, amount: float):
        if not self._simulate_payment_gateway(amount):
            raise PaymentError("Payment processing failed")

    def _simulate_payment_gateway(self, amount: float) -> bool:
        time.sleep(random.uniform(0.1, 0.5))  # Simulate network delay
        return True

    def _update_inventory(self, items: List[Dict[str, Any]]):
        with self.lock:
            for item in items:
                self.inventory[item['product_id']] -= item['quantity']

    def _send_confirmation_email(self, user_id: str):
        logging.info(f"Confirmation email sent to user {user_id}")

    def _log_audit(self, order_id: str, action: str):
        logging.info(f"Audit log: {action} for order {order_id}")

# Example Usage
order_manager = OrderManager()
try:
    order_data = {
        "user_id": "user_123",
        "items": [{"product_id": "product_1", "quantity": 2}],
        "total_value": 150.0
    }
    token = jwt.encode({"user_id": "user_123"}, "secret", algorithm="HS256")
    order = order_manager.process_order(order_data, token=token)
    print(order)
except Exception as e:
    print(f"Error: {e}")