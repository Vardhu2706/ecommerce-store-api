from datetime import datetime
from typing import Literal
from pydantic  import BaseModel


class Discount(BaseModel):
    id: str
    user_id: str
    triggered_by_order_id: str
    code: str | None = None
    percentage: float
    status: Literal['pending_approval', 'approved', 'rejected', 'used'] = 'pending_approval'
    used_in_order_id: str | None = None
    created_at: datetime
    approved_at: datetime | None = None