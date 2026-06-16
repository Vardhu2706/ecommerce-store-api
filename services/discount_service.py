"""
Discount lifecycle: 
Creation on Nth order, admin approval/rejection/revert, and redepmtion.
"""
import logging 
import config 
import store

from datetime import datetime, timezone
from uuid import uuid4
from models.discount import Discount


logger = logging.getLogger(__name__)


def create_pending_discount_if_eligible(user_id: str, order_id: str) -> Discount | None:
    """
    Create a pending discount after every Nth completed order.
    (Configured by DISCOUNT_EVERY_N)
    """
    count = store.user_order_counts.get(user_id, 0)
    if count == 0 or count % config.DISCOUNT_EVERY_N != 0:
        return None
    
    discount = Discount(
        id=str(uuid4()),
        user_id=user_id,
        triggered_by_order_id=order_id,
        percentage=config.DISCOUNT_PERCENTAGE,
        created_at=datetime.now(timezone.utc)
    )

    store.discounts[discount.id] = discount

    logger.info(
        'Discount created: discount_id=%s user_id=%s triggered_by_order_id=%s percentage=%.1f',
        discount.id,
        user_id,
        order_id,
        discount.percentage
    )

    return discount


def approve_discount(discount_id: str) -> Discount:
    """
    Generate a discount code and mark the discount as approved.
    Only valid from pending_approval.
    """
    discount = store.discounts.get(discount_id)

    if discount is None:
        raise KeyError(f'Discount {discount_id} not found')
    if discount.status != 'pending_approval':
        raise ValueError(f"Cannot approve discount with status '{discount.status}'")
    
    discount.code = str(uuid4())
    discount.status = 'approved'    
    discount.approved_at = datetime.now(timezone.utc)

    logger.info(
        'Discount approved: discount_id=%s user_id=%s code=%s',
        discount.id,
        discount.user_id,
        discount.code
    )

    return discount


def reject_discount(discount_id: str) -> Discount: 
    """
    Mark the discount as rejected. 
    Only valid from pending_approval.
    """
    discount = store.discounts.get(discount_id)

    if discount is None:
        raise KeyError(f'Discount {discount_id} not found')
    if discount.status != 'pending_approval':
        raise ValueError(f"Cannot reject discount with status '{discount.status}'")
    
    discount.status = 'rejected'
    
    logger.info(
        'Discount rejected: discount_id=%s user_id=%s',
        discount.id,
        discount.user_id
    )
    
    return discount


def revert_discount(discount_id: str) -> Discount:
    """
    Return a discount to pending_approval from approved or rejected.
    Cannot revert used discounts.
    """
    discount = store.discounts.get(discount_id)

    if discount is None:
        raise KeyError(f'Discount {discount_id} not found')
    if discount.status == 'used':
        raise ValueError('Cannot revert a used discount')
    
    prev_status = discount.status
    discount.status = 'pending_approval'
    discount.code = None
    discount.approved_at = None

    logger.info(
        'Discount reverted: discount_id=%s user_id=%s from_status=%s',
        discount.id,
        discount.user_id,
        prev_status
    )

    return discount


def get_redeemable_discount_for_user(user_id: str) -> Discount | None:
    """
    Return the oldest approved, unused discount for the user.
    """
    redeemable = [
        d for d in store.discounts.values()
        if d.user_id == user_id and d.status == 'approved' and d.used_in_order_id is None
    ]

    return min(redeemable, key=lambda d: d.created_at, default=None)