from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conint
import time

app = FastAPI()

class CalculationRequest(BaseModel):
    a: conint(strict=True)
    b: conint(strict=True)

@app.post("/add")
async def add_numbers(request: CalculationRequest):
    """
    Endpoint to add two numbers.

    Args:
        request (CalculationRequest): The request containing two integers to add.

    Returns:
        dict: A dictionary containing the result of the addition.
    """
    start_time = time.time()
    result = request.a + request.b
    response_time = (time.time() - start_time) * 1000
    if response_time > 100:
        raise HTTPException(status_code=500, detail="Response time exceeded 100ms")
    return {"result": result}

@app.post("/divide")
async def divide_numbers(request: CalculationRequest):
    """
    Endpoint to divide two numbers.

    Args:
        request (CalculationRequest): The request containing two integers to divide.

    Returns:
        dict: A dictionary containing the result of the division or an error message.
    """
    if request.b == 0:
        raise HTTPException(status_code=400, detail="Division by zero is not allowed")
    result = request.a / request.b
    return {"result": result}
