import pytest
from my_module import SimpleCalculatorService, OperationError

@pytest.fixture
def calculator_service():
    # Setup: Create an instance of the SimpleCalculatorService
    return SimpleCalculatorService()

def test_basic_simple_calculator_service_functionality(calculator_service):
    # Action: User performs Simple Calculator Service
    try:
        result = calculator_service.perform_operation(5, 3, 'add')
    except OperationError as e:
        pytest.fail(f"Operation failed with error: {e}")

    # Assertions
    assert result is not None, "Expected a result, but got None"
    assert isinstance(result, (int, float)), f"Expected result to be int or float, but got {type(result)}"
    assert result == 8, f"Expected result to be 8, but got {result}"