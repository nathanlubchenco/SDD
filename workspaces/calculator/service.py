from dataclasses import dataclass
from typing import Union

# Custom exception for validation errors
class ValidationError(Exception):
    pass

# Data model for User
@dataclass
class User:
    user_id: int
    name: str

# Manager class for Simple Calculator Service
class SimpleCalculatorService:
    def __init__(self):
        pass

    def perform_operation(self, user: User, operation: str, operand1: Union[int, float], operand2: Union[int, float]) -> Union[int, float]:
        """
        Perform a simple arithmetic operation.

        :param user: User performing the operation
        :param operation: The operation to perform ('add', 'subtract', 'multiply', 'divide')
        :param operand1: The first operand
        :param operand2: The second operand
        :return: The result of the operation
        :raises ValidationError: If the operation is invalid or division by zero is attempted
        """
        self._validate_user(user)
        self._validate_operation(operation)
        self._validate_operands(operand1, operand2, operation)

        if operation == 'add':
            return operand1 + operand2
        elif operation == 'subtract':
            return operand1 - operand2
        elif operation == 'multiply':
            return operand1 * operand2
        elif operation == 'divide':
            return operand1 / operand2

    def _validate_user(self, user: User) -> None:
        if not isinstance(user, User):
            raise ValidationError("Invalid user provided.")

    def _validate_operation(self, operation: str) -> None:
        if operation not in ['add', 'subtract', 'multiply', 'divide']:
            raise ValidationError(f"Invalid operation '{operation}'. Supported operations are: add, subtract, multiply, divide.")

    def _validate_operands(self, operand1: Union[int, float], operand2: Union[int, float], operation: str) -> None:
        if not isinstance(operand1, (int, float)) or not isinstance(operand2, (int, float)):
            raise ValidationError("Operands must be int or float.")
        if operation == 'divide' and operand2 == 0:
            raise ValidationError("Division by zero is not allowed.")

# Example usage
if __name__ == "__main__":
    user = User(user_id=1, name="Alice")
    calculator_service = SimpleCalculatorService()
    try:
        result = calculator_service.perform_operation(user, 'add', 10, 5)
        print(f"Result: {result}")
    except ValidationError as e:
        print(f"Error: {e}")