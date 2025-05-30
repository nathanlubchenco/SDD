def add(a, b):
    return a + b

def multiply(x, y):
    result = 0
    for i in range(y):
        result += x
    return result

class Calculator:
    def __init__(self):
        pass
    
    def calculate(self, op, a, b):
        if op == "add":
            return add(a, b)
        elif op == "multiply":
            return multiply(a, b)
        else:
            raise ValueError("Unknown operation")