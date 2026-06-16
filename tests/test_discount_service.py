"""
Unit tests for discount_service - covers the full lifecycle: creation, approval, rejection, revert, and redemption.
"""
import pytest
import config
import store

from datetime import datetime, timezone
from models.product import Product
from services import discount_service


@pytest.fixture(autouse=True)
def reset_store():
    """
    Reset the in-memory store to clean a state before every test.
    """
    store.products = {'prod_1': Product(id='prod_1', name='Widget', price=10.0)}
    store.carts = {}
    store.active_carts = {}
    store.orders = {}
    store.discounts = {}
    store.user_order_counts = {}


def test_nth_order_triggers_discount_creation():
    """
    
    """
    store.user_order_counts['user_1'] = 5
    discount_service.create_pending_discount_if_eligible('user_1', 'order_5')    
    pending = [d for d in store.discounts.values() if d.user_id == 'user_1']
    
    assert len(pending) == 1
    assert pending[0].status == 'pending_approval'
    assert pending[0].code is None


def test_each_eligible_order_creates_a_separate_discount():
    """
    Each Nth-order milestone produces its own distinct discount, not a replacement of the previous one.
    """
    store.user_order_counts['user_1'] = 5
    discount_service.create_pending_discount_if_eligible('user_1', 'order_5')
    store.user_order_counts['user_1'] = 10
    discount_service.create_pending_discount_if_eligible('user_1', 'order_10')
    pending = [d for d in store.discounts.values() if d.user_id == 'user_1']

    assert len(pending) == 2
    assert {d.triggered_by_order_id for d in pending} == {'order_5', 'order_10'}


def test_approve_generates_codes():
    """
    Approving a discount sets its status to 'approved' and populates code and approved_at.
    """
    store.user_order_counts["user_1"] = 5
    discount_service.create_pending_discount_if_eligible("user_1", "order_5")
    disc_id = list(store.discounts.keys())[0]
    disc = discount_service.approve_discount(disc_id)

    assert disc.status == "approved"
    assert disc.code is not None
    assert disc.approved_at is not None


def test_rejects_sets_status():
    """
    Rejecting a pending discount marks it 'rejected' without generating a code.
    """
    store.user_order_counts["user_1"] = 5
    discount_service.create_pending_discount_if_eligible("user_1", "order_5")
    disc_id = list(store.discounts.keys())[0]
    disc = discount_service.reject_discount(disc_id)

    assert disc.status == "rejected"


def test_revert_from_approved_resets_code_and_status():
    """
    Reverting an approved discount clears its code and approved_at, returning it to pending_approval.
    """
    store.user_order_counts['user_1'] = 5
    discount_service.create_pending_discount_if_eligible('user_1', 'order_5')
    discount_id = list(store.discounts.keys())[0]
    discount = discount_service.revert_discount(discount_id)

    assert discount.status == 'pending_approval'
    assert discount.code is None
    assert discount.approved_at is None


def test_revert_from_rejected_resets_status():
    """
    A rejected discount can be reverted back to pending_approval, allowing for review again.
    """
    store.user_order_counts['user_1'] = 5
    discount_service.create_pending_discount_if_eligible('user_1', 'order_5')
    discount_id = list(store.discounts.keys())[0]
    discount_service.reject_discount(discount_id)
    discount = discount_service.revert_discount(discount_id)

    assert discount.status == 'pending_approval'


def test_cannot_revert_used_discount():
    """
    A discount that has already been used for an order cannot be reverted.
    """
    store.user_order_counts['user_1'] = 5
    discount_service.create_pending_discount_if_eligible('user_1', 'order_5')
    discount_id = list(store.discounts.keys())[0]
    store.discounts[discount_id].status = 'used'

    with pytest.raises(ValueError):
        discount_service.revert_discount(discount_id)


def test_discount_percentage_copied_from_config_at_creation():
    """
    The percentage is snapshotted form config at creation time.
    Later config changes don't affect it.
    """
    original = config.DISCOUNT_PERCENTAGE
    config.DISCOUNT_PERCENTAGE = 25.0
    store.user_order_counts['user_1'] = 5
    discount_service.create_pending_discount_if_eligible('user_1', 'order_5')
    discount = list(store.discounts.values())[0]

    assert discount.percentage == 25.0
    config.DISCOUNT_PERCENTAGE = original


def test_get_redeemable_discount_returns_oldest_when_multiple_approved():
    """
    When the user has multiple approved discounts, the oldest one is returned first (FIFO).
    """
    store.user_order_counts['user_1'] = 5
    discount_service.create_pending_discount_if_eligible('user_1', 'order_5')
    store.user_order_counts['user_1'] = 10
    discount_service.create_pending_discount_if_eligible('user_1', 'order_10')

    ids = list(store.discounts.keys())
    discount_service.approve_discount(ids[0])
    discount_service.approve_discount(ids[1])
    discount = discount_service.get_redeemable_discount_for_user('user_1')

    assert discount.triggered_by_order_id == 'order_5'


def test_get_redeemable_discount_returns_none_when_none_approved():
    """
    A discount in pending_approval is not redeemable, the function returns None.
    """
    store.user_order_counts['user_1'] = 5
    discount_service.create_pending_discount_if_eligible('user_1', 'order_5')
    
    assert discount_service.get_redeemable_discount_for_user('user_1') is None