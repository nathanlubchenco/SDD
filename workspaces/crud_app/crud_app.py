from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

app = FastAPI()

data_store: Dict[int, str] = {}


class DataItem(BaseModel):
    id: int
    value: str


@app.post("/data/", response_model=DataItem)
def add_data(item: DataItem) -> DataItem:
    """
    Add a new data item to the data store.

    :param item: DataItem object containing id and value
    :return: The added DataItem
    """
    if item.id in data_store:
        raise HTTPException(status_code=400, detail="Item already exists")
    data_store[item.id] = item.value
    return item


@app.get("/data/{item_id}", response_model=DataItem)
def get_data(item_id: int) -> DataItem:
    """
    Retrieve a data item from the data store by its ID.

    :param item_id: ID of the data item to retrieve
    :return: The requested DataItem
    """
    if item_id not in data_store:
        raise HTTPException(status_code=404, detail="Item not found")
    return DataItem(id=item_id, value=data_store[item_id])


@app.put("/data/{item_id}", response_model=DataItem)
def update_data(item_id: int, item: DataItem) -> DataItem:
    """
    Update an existing data item in the data store.

    :param item_id: ID of the data item to update
    :param item: DataItem object containing updated value
    :return: The updated DataItem
    """
    if item_id not in data_store:
        raise HTTPException(status_code=404, detail="Item not found")
    data_store[item_id] = item.value
    return item


@app.delete("/data/{item_id}", response_model=Optional[DataItem])
def delete_data(item_id: int) -> Optional[DataItem]:
    """
    Delete a data item from the data store by its ID.

    :param item_id: ID of the data item to delete
    :return: The deleted DataItem
    """
    if item_id not in data_store:
        raise HTTPException(status_code=404, detail="Item not found")
    deleted_item = DataItem(id=item_id, value=data_store.pop(item_id))
    return deleted_item
