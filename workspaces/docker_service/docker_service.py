from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import uvicorn
import os

app = FastAPI(title='My FastAPI Service', version='1.0.0')

class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

items: Dict[int, Item] = {}

@app.get('/')
async def read_root() -> Dict[str, str]:
    return {'Hello': 'World'}

@app.get('/items/{item_id}')
async def read_item(item_id: int) -> Dict[str, Item]:
    if item_id in items:
        return {'item': items[item_id]}
    raise HTTPException(status_code=404, detail='Item not found')

@app.post('/items/')
async def create_item(item_id: int, item: Item) -> Dict[str, Item]:
    if item_id in items:
        raise HTTPException(status_code=400, detail='Item already exists')
    items[item_id] = item
    return {'item': item}

@app.get('/health')
async def health_check() -> Dict[str, str]:
    return {'status': 'healthy'}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 8000)))