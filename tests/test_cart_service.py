"""
Unit tests for cart_service - covers lazy creation, quantity merging, CRUD and edge cases.
"""
import pytest
import store

from models.product import Product
from services import cart_service


@pytest.fixture(autouse=True)
def reset_store():
    """
    Reset the in-memory store to clean state before every test.
    """
    store.products = {
        'prod_1': Product(id='prod_1', name='Widget', price=10.0),
        'prod_2': Product(id='prod_2', name='Gadget', price=20.0),
    }
    store.carts = {}
    store.active_carts = {}
    store.orders = {}
    store.discounts = {}
    store.user_order_counts = {}


def test_add_item_creates_cart_lazily():
    """
    A cart is only created when the first item is added, not on user creation.
    """
    cart = cart_service.add_item('user_1', 'prod_1', 1)
    
    assert cart.id in store.carts
    assert store.active_carts['user_1'] == cart.id
    assert len(cart.items) == 1


def test_add_same_item_twice_increases_quantity():
    """
    Adding a product that is already in the cart merges quantities rather than duplicating the line.
    """
    cart_service.add_item('user_1', 'prod_1', 2)
    cart = cart_service.add_item('user_1', 'prod_1', 3)

    assert len(cart.items) == 1
    assert cart.items[0].quantity == 5


def test_update_item_quantity():
    """
    update_item replaces the quantity rather than adding to it.
    """
    cart_service.add_item('user_1', 'prod_1', 2)
    cart = cart_service.update_item('user_1', 'prod_1', 7)

    assert cart.items[0].quantity == 7


def test_remove_item():
    """
    Removing one item leaves other items in cart untouched.
    """
    cart_service.add_item('user_1', 'prod_1', 1)
    cart_service.add_item('user_1', 'prod_2', 1)
    cart = cart_service.remove_item('user_1', 'prod_1')

    assert len(cart.items) == 1
    assert cart.items[0].product_id == 'prod_2'


def test_clear_cart():
    """
    Clearning removes all items but keeps the cart active.
    (Status stays 'active')
    """
    cart_service.add_item('user_1', 'prod_1', 2)
    cart_service.add_item('user_1', 'prod_2', 1)
    cart = cart_service.clear_cart('user_1')

    assert cart.items == []
    assert cart.status == 'active'


def test_cannot_update_item_not_in_cart():
    """
    Updating a product that was never added raises KeyError.
    """
    cart_service.add_item('user_1', 'prod_1', 1)
    with pytest.raises(KeyError):
        cart_service.update_item('user_1', 'prod_2', 5)


def test_cannot_remove_item_not_in_cart():
    """
    Removing a product that was never added raises KeyError.
    """
    cart_service.add_item('user_1', 'prod_1', 1)
    with pytest.raises(KeyError):
        cart_service.remove_item('user_1', 'prod_2')


def test_checked_out_cart_is_not_reused():
    """
    After checkout removes a cart from active_carts, the next add_item creates a new cart.
    """
    cart_service.add_item('user_1', 'prod_1', 1)
    first_cart_id = store.active_carts['user_1']
    store.carts[first_cart_id].status = 'checked_out'
    del store.active_carts['user_1']

    cart = cart_service.add_item('user_1', 'prod_2', 1)
    assert cart.id != first_cart_id