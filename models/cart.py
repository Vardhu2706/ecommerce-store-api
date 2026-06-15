from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class CartItem(BaseModel):
    product_id: str
    quantity: int
    price_at_add: float


class Cart(BaseModel):
    id: str
    user_id: str
    items: list[CartItem] = []
    status: Literal['active', 'checked_out'] = 'active'
    create_at: datetime