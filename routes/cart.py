"""
Cart management endpoints.
The caller is identified by the X-User-Id request header.
"""
import logging

from utils.helpers import build_enriched_items
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from services import cart_service


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Cart"])


def _build_cart_response(user_id: str):
    """
    Build a JSON-serializable cart payload enriched with product names and subtotals.
    """
    cart = cart_service.get_active_cart(user_id)
    if cart is None:
        return {
            'cart_id': None,
            'items': [],
            'total': 0.0
        }
    
    items = build_enriched_items(cart.items)
    total = round(sum(i['subtotal'] for i in items), 2)
    return {
        'cart_id': cart.id,
        'items': items,
        'total': total
    }


def _get_required_user_id(x_user_id: str | None) -> str:
    """
    Validate presence of X-User-Id header and return it.
    Raises 400 if missing.
    """
    if not x_user_id:
        logger.warning('Cart request rejected: missing X-User-Id header')
        raise HTTPException(
            status_code=400,
            detail='X-User-Id header is required'
        )
    
    return x_user_id


class AddItemRequest(BaseModel):
    product_id: str
    quantity: int


class UpdateItemRequest(BaseModel):
    quantity: int


@router.get('/cart')
def get_cart(x_user_id: str | None = Header(default=None)):
    """
    Return the user's current cart contents, or an empty cart if none exists.
    """
    user_id = _get_required_user_id(x_user_id)
    return _build_cart_response(user_id)


@router.post('/cart/items')
def add_item(body: AddItemRequest, x_user_id: str | None = Header(default=None)):
    """
    Add a product to the cart, or increment its quantity if it is alreadt present.
    """
    user_id = _get_required_user_id(x_user_id)
    if body.quantity < 1:
        logger.warning('Add item rejected: invalid quantity=%s user_id=%s', body.quantity, user_id)
        raise HTTPException(
            status_code=400,
            detail='Quantity must be at least 1'
        )
    
    try:
        cart_service.add_item(user_id, body.product_id, body.quantity)
    except KeyError as e:
        logger.warning('Add item failed: user_id=%s product_id=%s error=%s', user_id, body.product_id, e)
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    
    return _build_cart_response(user_id)


@router.patch('/cart/items/{product_id}')
def update_item(product_id: str, body: UpdateItemRequest, x_user_id: str | None = Header(default=None)):
    """
    Set an exact quantity for an existing cart item.
    Returns 404 if the item is not in the cart.
    """
    user_id = _get_required_user_id(x_user_id)

    if body.quantity < 1:
        logger.warning('Update item rejected: invalid quantity=%d user_id=%s', body.quantity, user_id)
        raise HTTPException(
            status_code=400,
            detail='Quantity must be at least 1'
        )
    
    try:
        cart_service.update_item(user_id, product_id, body.quantity)
    except KeyError as e:
        logger.warning('Update item failed: user_id=%s product_id=%s error=%s', user_id, product_id, e)
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    
    return _build_cart_response(user_id)


@router.delete('/cart/items/{product_id}')
def remove_item(product_id: str, x_user_id: str | None = Header(default=None)):
    """
    Remove a single product line from the cart entirely.
    """
    user_id = _get_required_user_id(x_user_id)

    try:
        cart_service.remove_item(user_id, product_id)
    except KeyError as e:
        logger.warning('Remove item failed: user_id=%s product_id=%s error=%s', user_id, product_id, e)
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    
    return _build_cart_response(user_id)

@router.delete('/cart')
def clear_cart(x_user_id: str | None = Header(default=None)):
    """
    Remove all items from the cart without checking it out.
    """
    user_id = _get_required_user_id(x_user_id)

    try:
        cart_service.clear_cart(user_id)    
    except KeyError as e:
        logger.warning('Clear cart failed: user_id=%s error=%s', user_id, e)
        raise HTTPException(
            status_code=404, 
            detail=str(e)
        )
    
    return {'message': 'Cart cleared'}