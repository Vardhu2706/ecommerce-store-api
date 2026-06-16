"""
Checkout endpoints for previewing and confirming an order.
"""
import logging

from fastapi import APIRouter, Header, HTTPException
from services import checkout_service


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Checkout"])


def _get_required_user_id(x_user_id: str | None) -> str:
    """
    Validate presence of X-User-Id header; raises 400 if missing.
    """
    if not x_user_id:
        logger.warning('Checkout request rejected: missing X-User-Id header')
        raise HTTPException(
            status_code=400,
            detail='X-User-Id header is required'
        )
    return x_user_id


@router.get('/checkout/preview')
def preview(x_user_id: str | None = Header(default=None)):
    """
    Show what the user would pay, including any applicable discount, without placing the order.
    """
    user_id = _get_required_user_id(x_user_id)

    try:
        return checkout_service.get_checkout_preview(user_id)
    except ValueError as e:
        logger.warning('Checkout preview failed: user_id=%s error=%s', user_id, e)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    

@router.post('/checkout/confirm')
def confirm(x_user_id: str | None = Header(default=None)):
    """
    Place the order, apply any approved discount, and trigger post-checkout side effects.
    """
    user_id = _get_required_user_id(x_user_id)

    try:
        order = checkout_service.place_order(user_id)
    except ValueError as e:
        logger.warning('Checkout confirm failed: user_id=%s error=%s', user_id, e)
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        'order_id': order.id,
        'items': order.items,
        'total': order.total,
        'discount_applied': order.discount_amount > 0,
        'discount_amount': order.discount_amount,
        'final_total': order.final_total,
        'created_at': order.created_at
    }