"""
Admin-only endpoints for discount lifecycle management, order inspection and platfor stats.
"""
import logging
import config
import store

from fastapi import APIRouter, Header, HTTPException, Query
from services import discount_service
from typing import Optional


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Admin"])


def _validate_admin_key(x_admin_key: str | None) -> None:
    """
    Raise 401 if the X-Admin-Key header is missing or does not match config.
    """
    if x_admin_key != config.ADMIN_KEY:
        logger.warning('Admin auth failed: invalid or missing X-Admin-Key')
        raise HTTPException(
            status_code=401,
            detail='Invalid or missing admin key'
        )


# Discounts

@router.get('/discounts')
def list_discounts(
    status: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    x_admin_key: str | None = Header(default=None)
):
    """
    Return paginated discounts, optionally filtered by status and/or user_id.
    """
    _validate_admin_key(x_admin_key)

    results = list(store.discounts.values())
    if status:
        results = [d for d in results if d.status == status]
    if user_id:
        results = [d for d in results if d.user_id == user_id]

    total = len(results)
    start = (page - 1) * page_size

    return {
        'total': total,
        'page': page,
        'page_size': page_size,
        'results': results[start: start + page_size]
    }


@router.patch('/discounts/{discount_id}/approve')
def approve_discount(discount_id: str, x_admin_key: str | None = Header(default=None)):
    """Approve a pending discount, generating its redemption code."""
    _validate_admin_key(x_admin_key)

    try:
        discount = discount_service.approve_discount(discount_id)
    except KeyError as e:
        logger.warning('Approve discount failed: discount_id=%s error=%s', discount_id, e)
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning('Approve discount rejected: disocunt_id=%s error=%s', discount_id, e)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
    return {
        'id': discount.id,
        'user_id': discount.user_id,
        'code': discount.code,
        'status': discount.status,
        'approved_at': discount.approved_at
    }


@router.patch('/discounts/{discount_id}/reject')
def reject_discount(discount_id: str, x_admin_key: str | None = Header(default=None)):
    """
    Reject a pending discount, preventing it from being redeemed.
    """
    _validate_admin_key(x_admin_key)

    try:
        discount = discount_service.reject_discount(discount_id)
    except KeyError as e:
        logger.warning('Reject discount failed: discoun_id=%s error=%s', discount_id, e)
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning('Reject discount rejected: discount_id=%s error=%s', discount_id, e)
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        'id': discount.id,
        'status': discount.status
    }


@router.patch('/discounts/{discount_id}/revert')
def revert_discount(discount_id: str, x_admin_key: str | None = Header(default=None)):
    """
    Revert an approved or rejected discount back to pending_approval.
    """
    _validate_admin_key(x_admin_key)

    try:
        discount = discount_service.revert_discount(discount_id)
    except KeyError as e:
        logger.warning('Revert discount failed: discount_id=%s error=%s', discount_id, e)
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning('Revert discount rejected: discount_id=%s error=%s', discount_id, e)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
    return {
        'id': discount.id,
        'status': discount.status,
        'code': discount.code
    }


# Orders

@router.get('/orders')
def list_orders(
    user_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1),
    x_admin_key: str | None = Header(default=None)
):
    """
    Return paginated orders across all users, optionally filtered by user_id.
    """
    _validate_admin_key(x_admin_key)

    results = list(store.orders.values())
    if user_id:
        results = [o for o in results if o.user_id == user_id]
    total = len(results)
    start = (page - 1) * page_size
    page_orders = results[start: start + page_size]

    return {
        'total': total,
        'page': page,
        'page_size': page_size,
        'results': [
            {
                "order_id": o.id,
                "user_id": o.user_id,
                "total": o.total,
                "discount_applied": o.discount_amount > 0,
                "discount_amount": o.discount_amount,
                "final_total": o.final_total,
                "created_at": o.created_at,
            }
            for o in page_orders
        ]
    }


# Stats

@router.get('/stats')
def stats(x_admin_key: str | None = Header(default=None)):
    """
    Return aggregated platform metrics: revenue, item counts, and per-discount savings.
    """
    _validate_admin_key(x_admin_key)

    all_orders = list(store.orders.values())
    used_discounts = [
        d for d in store.discounts.values()
        if d.status == 'used' and d.used_in_order_id is not None
    ]

    return {
        'total_orders': len(all_orders),
        'total_items_purchased': sum(i.quantity for o in all_orders for i in o.items),
        'total_revenue': round(sum(o.final_total for o in all_orders), 2),
        'total_discounts_given': len(used_discounts),
        'total_discount_amount': round(sum(o.discount_amount for o in all_orders), 2),
        'discount_summary': [
            {
                'discount_id': d.id,
                'user_id': d.user_id,
                'order_id': d.used_in_order_id,
                'amount_saved': store.orders[d.used_in_order_id].discount_amount
            }
            for d in used_discounts
        ]
    }