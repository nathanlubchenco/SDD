from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError
from typing import Union
import time

app = FastAPI()

class OperationRequest(BaseModel):
    a: Union[int, float]
    b: Union[int, float]

@app.post("/add")
async def add_numbers(request: OperationRequest):
    """
    Endpoint to add two numbers.
    """
    start_time = time.time()
    result = request.a + request.b
    response_time = (time.time() - start_time) * 1000
    if response_time > 100:
        raise HTTPException(status_code=500, detail="Response time exceeded 100ms")
    return {"result": result, "response_time_ms": response_time}

@app.post("/divide")
async def divide_numbers(request: OperationRequest):
    """
    Endpoint to divide two numbers.
    """
    try:
        if request.b == 0:
            raise ValueError("Division by zero is not allowed.")
        result = request.a / request.b
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"result": result}

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    """
    Handle validation errors gracefully.
    """
    return HTTPException(status_code=422, detail="Invalid input")
