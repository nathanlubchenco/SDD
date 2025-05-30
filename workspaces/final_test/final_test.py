from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
import time

app = FastAPI()

class CalculationRequest(BaseModel):
    number1: float
    number2: float

    @validator('number1', 'number2')
    def validate_numbers(cls, value):
        if not isinstance(value, (int, float)):
            raise ValueError('Inputs must be numbers')
        return value

@app.post("/add")
async def add_numbers(request: CalculationRequest):
    """
    Endpoint to add two numbers.
    Returns the sum of the numbers if successful.
    """
    start_time = time.time()
    result = request.number1 + request.number2
    response_time = (time.time() - start_time) * 1000
    if response_time > 100:
        raise HTTPException(status_code=500, detail="Response time exceeded")
    return {"result": result}

@app.post("/divide")
async def divide_numbers(request: CalculationRequest):
    """
    Endpoint to divide two numbers.
    Returns the quotient if successful, or an error message if division by zero is attempted.
    """
    try:
        if request.number2 == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        result = request.number1 / request.number2
    except ZeroDivisionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"result": result}
