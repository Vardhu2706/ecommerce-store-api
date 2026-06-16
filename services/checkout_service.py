""""
Order placement with discount application and post-checkout side effects.
"""
import logging
import store

from datetime import datetime, timezone
from uuid import uuid4
from models.order import Order
from services import discount_service


logger = logging.getLogger(__name__)


def get_checkout_preview(user_id: str) -> dict:
    """
    Return a cost summary for the active cart without committing the order.
    Includes the oldest redeemable discount if one is available.
    """
    cart_id = store.active_carts.get(user_id)
    if not cart_id:
        raise ValueError('No active cart')
    
    cart = store.carts[cart_id]
    if not cart.items:
        raise ValueError('Cart is empty')
    
    total = round(sum(i.quantity * i.price_at_add for i in cart.items), 2)
    discount = discount_service.get_redeemable_discount_for_user(user_id)

    result = {
        'cart_id': cart_id,
        'items': cart.items,
        'total': total,
        'discount': None
    }

    if discount:
        amount = round(total * discount.percentage/100, 2)
        result['discount'] = {
            'id': discount.id,
            'code': discount.code,
            'percentage': discount.percentage,
            'discount_amount': amount,
            'final_total': round(total - amount, 2),
        }
    return result


def place_order(user_id: str) -> Order:
    """
    Convert the active cart into an order and trigger post-checkout side effects.
    The discount is re-validated immediately before use to guard against a race where another request consumed it between preview and confirm.
    """
    cart_id = store.active_carts.get(user_id)
    if not cart_id:
        raise ValueError('No active cart')
    
    cart = store.carts[cart_id]
    if not cart.items:
        raise ValueError('Cart is empty')
    
    total = round(sum(i.quantity * i.price_at_add for i in cart.items), 2)

    # Fetch discount and re-validate atomically
    discount = discount_service.get_redeemable_discount_for_user(user_id)
    discount_amount = 0.0
    discount_id = None

    if discount:
        # Guard against concurrent use between preview and confirm.
        if discount.status == 'approved' and discount.used_in_order_id is None:
            discount_amount = round(total * discount.percentage / 100, 2)
            discount_id = discount.id
        else:
            logger.warning(
                'Discount skipped at confirm (used concurrently): discount_id=%s user_id=%s',
                discount.id,
                user_id
            )

    final_total = round(total - discount_amount, 2)
    order = Order(
        id=str(uuid4()),
        user_id=user_id,
        cart_id=cart.id,
        items=list(cart.items),
        total=total,
        discount_id=discount_id,
        discount_amount=discount_amount,
        final_total=final_total,
        created_at=datetime.now(timezone.utc)
    )
    store.orders[order.id] = order

    # Post-checkout side effects 
    cart.status = 'checked_out'
    del store.active_carts[user_id]
    store.user_order_counts[user_id] = store.user_order_counts.get(user_id, 0) + 1

    if discount_id:
        discount.status = 'used'
        discount.used_in_order_id = order.id

    discount_service.create_pending_discount_if_eligible(user_id, order.id)

    logger.info(
        'Order placed: order_id=%s user_id=%s total=%.2f discount_amount=%.2f final_total=%.2f',
        order.id,
        user_id,
        total,
        discount_amount,
        final_total        
    )
    return order