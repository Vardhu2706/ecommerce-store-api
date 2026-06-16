"""
Cart CRUD operations.
Carts are created lazily - none exist until the first item is added.
"""
import logging 
import store

from datetime import datetime, timezone
from uuid import uuid4
from models.cart import Cart, CartItem


logger = logging.getLogger(__name__)


def _get_or_create_cart(user_id: str) -> Cart:
    """
    Return the user's active cart, create a fresh one if none exists.
    """
    cart_id = store.active_carts.get(user_id)
    if cart_id and cart_id in store.carts:
        return store.carts[cart_id]
    
    cart = Cart(id=str(uuid4()), user_id=user_id, created_at=datetime.now(timezone.utc))
    store.carts[cart.id] = cart
    store.active_carts[user_id] = cart.id

    logger.info('Cart created: cart_id=%s user_id=%s', cart.id, user_id)
    return cart


def _get_active_cart(user_id: str) -> Cart | None:
    """
    Return the user's active cart, or None if no cart exists.
    """
    cart_id = store.active_carts.get(user_id)
    return store.carts.get(cart_id) if cart_id else None


def add_item(user_id: str, product_id: str, quantity: int) -> Cart:
    """
    Add a product to the cart.
    Increments quantity if the product is already present.
    """
    product = store.products.get(product_id)
    if product is None:
        raise KeyError(f'Product {product_id} not found.')
    if quantity < 1:
        raise ValueError('Quantity must be at least 1.')
    
    cart = _get_or_create_cart(user_id)

    for item in cart.items:
        if item.product_id == product_id:
            item.quantity += quantity
            logger.info(
                'Cart item quantity increased: user_id%s product_id=%s new_quantity=%d',
                user_id,
                product_id,
                item.quantity
            )
            return cart
        
    cart.items.append(
        CartItem(
            product_id=product_id,
            quantity=quantity,
            price_at_add=product.price
        )
    )

    logger.info(
        'Cart item added: user_id=%s product_id=%s quantity=%s price=%.2f',
        user_id,
        product_id,
        quantity,
        product.price
    )

    return cart


def update_item(user_id: str, product_id: str, quantity: int) -> Cart:
    """
    Replace the quantity of an existing cart item.
    Raises KeyError if cart or item is missing.
    """
    if quantity < 1:
        raise ValueError('Quantity must be at least 1.')
    
    cart = _get_active_cart(user_id)
    if cart is None:
        raise KeyError('No active cart.')
    
    for item in cart.items:
        if item.product_id == product_id:
            item.quantity = quantity
            logger.info(
                'Cart item updated: user_id=%s product_id=%s quantity=%d',
                user_id,
                product_id,
                quantity
            )
            return cart
        
    raise KeyError(f'Product {product_id} not in cart')


def remove_item(user_id: str, product_id: str) -> Cart:
    """
    Remove a single product line from the the cart.
    Raises KeyError if not found.
    """
    cart = _get_active_cart(user_id)
    if cart is None:
        raise KeyError('No active carts.')
    
    for item in cart.items:
        if item.product_id == product_id:
            cart.items.remove(item)
            logger.info('Cart item removed: user_id=%s product_id=%s', user_id, product_id)
            return cart
        
    raise KeyError(f'Product {product_id} not in cart.')


def clear_cart(user_id: str) -> Cart:
    """
    Empty all items from the cart without changing its status or closing it.
    """
    cart = _get_active_cart(user_id)
    if cart is None:
        raise KeyError('No active cart.')
    
    cart.items.clear()
    logger.info('Cart cleared: user_id=%s cart_id=%s', user_id, cart.id)
    return cart


def get_active_cart(user_id: str) -> Cart | None:
    """
    Public accessor for the user's active cart.
    Returns None if none exists.
    """
    return _get_active_cart(user_id)