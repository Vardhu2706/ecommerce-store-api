"""
Product listing endpoint.
"""
import logging
import store

from fastapi import APIRouter


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Products"])


@router.get('/products')
def list_products():
    """
    Return all available products from the in-memory catalog.
    """
    return {
        'products': list(store.products.values())
    }