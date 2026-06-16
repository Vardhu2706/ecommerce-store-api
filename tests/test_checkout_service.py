"""
Unit tests for checkout_service - covers discount application, order_count and concurrent-use safety.
"""
import pytest
import config
import store

from models.cart import Cart, CartItem
from models.discount import Discount
from models.product import Product
from services import checkout_service
from datetime import datetime, timezone
from uuid import uuid4


@pytest.fixture(autouse=True)
def reset_store():
    """
    Reset the in-memory store to a clean state before every test.
    """
    store.products = {'prod_1': Product(id='prod_1', name='widget', price=10.0)}
    store.carts = {}
    store.active_carts = {}
    store.orders = {}
    store.discounts = {}
    store.user_order_counts = {}


def _active_cart(user_id: str, items: list[CartItem]) -> Cart:
    """
    Register a pre-built cart as the user's active cart in the store.
    """
    cart = Cart(id='cart_1', user_id=user_id, items=items, created_at=datetime.now(timezone.utc))
    store.carts[cart.id] = cart
    store.active_carts[user_id] = cart.id

    return cart


def _approved_discount(user_id: str) -> Discount:
    """
    Insert a pre-approved 10% discount into the store for the given user.
    """
    discount = Discount(
        id='disc_1',
        user_id=user_id,
        triggered_by_order_id='order_5',
        code=str(uuid4()),
        percentage=10.0,
        status='approved',
        created_at=datetime.now(timezone.utc),
        approved_at=datetime.now(timezone.utc)
    )
    store.discounts[discount.id] = discount
    return discount

def test_checkout_applies_approved_discount():
    """
    An approved discount is deducted from the order total and recorded on the order.
    """
    _active_cart('user_1', [CartItem(product_id='prod_1', quantity=2, price_at_add=10.0)])
    _approved_discount('user_1')
    order = checkout_service.place_order('user_1')

    assert order.discount_amount == 2.0
    assert order.final_total == 18.0
    assert order.discount_id == 'disc_1'


def test_checkout_with_no_discount_returns_full_total():
    """
    When no discount is available the final total equals the cart total.
    """
    _active_cart('user_1', [CartItem(product_id='prod_1', quantity=3, price_at_add=10.0)])
    order = checkout_service.place_order('user_1')

    assert order.total == 30.0
    assert order.discount_amount == 0.0
    assert order.final_total == 30.0


def test_discount_marked_as_used_after_discount():
    """
    A consumed discount is flipped to 'used' and linked to resulting order.
    """
    _active_cart('user_1', [CartItem(product_id='prod_1', quantity=1, price_at_add=10.0)])
    discount = _approved_discount('user_1')
    order = checkout_service.place_order('user_1')

    assert store.discounts[discount.id].status == 'used'
    assert store.discounts[discount.id].used_in_order_id == order.id


def test_order_count_incremented_after_checkout():
    """
    user_order_counts is incremented after each successful checkout to drive discount eligibility.
    """
    _active_cart('user_1', [CartItem(product_id='prod_1', quantity=1, price_at_add=10.0)])
    checkout_service.place_order('user_1')

    assert store.user_order_counts['user_1'] == 1


def test_nth_order_creates_pending_discount():
    """
    Completing the Nth order (per DISCOUNT_EVERY_N) creates one pending discount awaiting adming approval.
    """
    store.user_order_counts['user_1'] = config.DISCOUNT_EVERY_N - 1
    _active_cart('user_1', [CartItem(product_id='prod_1', quantity=1, price_at_add=10.0)])
    checkout_service.place_order('user_1')

    assert store.user_order_counts['user_1'] == config.DISCOUNT_EVERY_N
    pending = [d for d in store.discounts.values() if d.status == 'pending_approval']
    
    assert len(pending) == 1


def test_checkout_fails_on_empty_cart():
    """
    Confirming a checkout on an empty cart raises ValueError
    """
    _active_cart('user_1', [])
    with pytest.raises(ValueError, match='empty'):
        checkout_service.place_order('user_1')


def test_checkout_fails_on_no_active_cart():
    """
    Confirming a checkout when no cart exists raises ValueError
    """
    with pytest.raises(ValueError, match='No active cart'):
        checkout_service.place_order('user_1')


def test_checkout_falls_back_gracefully_if_discount_used_concurrently():
    """
    If a discount is consumed between preview and confirm, the order proceeds at fill price.
    """
    _active_cart('user_1', [CartItem(product_id='prod_1', quantity=1, price_at_add=10.0)])
    discount = _approved_discount('user_1')

    # Simulate concurrent use
    discount.status = 'used'
    discount.used_in_order_id = 'some_other_order'
    order = checkout_service.place_order('user_1')

    assert order.discount_amount == 0.0
    assert order.final_total == order.total
    assert order.discount_id is None