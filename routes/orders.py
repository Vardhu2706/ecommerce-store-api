"""
Order listing endpoint with dual auth:
    - admin key returns all orders,
    - user header returns own.
"""
import logging
import config
import store

from fastapi import APIRouter, Header, HTTPException, Query
from typing import Optional


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Orders"])


@router.get('/orders')
def list_orders(
    x_user_id: Optional[str] = Header(default=None),
    x_admin_key: Optional[str] = Header(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100)
):
    """
    Return paginated orders.
    Adming key grants access to all orders; user header filters to own orders.
    """
    if x_admin_key is not None:
        if x_admin_key != config.ADMIN_KEY:
            logger.warning("Admin auth failed on /orders: invalid X-Admin-Key")
            raise HTTPException(
                status_code=401, 
                detail='Invalid admin key'
            )
        all_orders = list(store.orders.values())
    elif x_user_id is not None:
        all_orders = [o for o in store.orders.values() if o.user_id == x_user_id]
    else:
        logger.warning("Orders request rejected: missing X-User-Id header")
        raise HTTPException(
            status_code=400,
            detail='X-User-Id header is required'
        )
    
    total = len(all_orders)
    start = (page - 1) * page_size
    page_orders = all_orders[start: start + page_size]

    return {
        'total': total,
        'page': page,
        'page_size': page_size,
        'orders': [
            {
                'order_id': o.id,
                'items': o.items,
                'total': o.total,
                'discount_applied': o.discount_amount > 0,
                'discount_amount': o.discount_amount,
                'final_total': o.final_total,
                'created_at': o.created_at
            }
            for o in page_orders
        ]
    }