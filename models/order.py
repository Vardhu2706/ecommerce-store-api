from datetime import datetime
from pydantic import BaseModel
from models.cart import CartItem


class Order(BaseModel):
    id: str
    user_id: str
    cart_id: str
    items: list[CartItem]
    total: float
    discount_id: str | None = None
    discount_amount: float = 0.0
    final_total: float
    created_at: datetime