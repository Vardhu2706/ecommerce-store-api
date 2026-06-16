"""
Shared response-building helpers for routes.
"""
import store


def build_enriched_items(items):
    """
    Convert CartItem objects into dicts enriched with product name and subtotal.
    """
    return [
        {
            "product_id": item.product_id,
            "name": store.products[item.product_id].name if item.product_id in store.products else item.product_id,
            "quantity": item.quantity,
            "price_at_add": item.price_at_add,
            "subtotal": round(item.quantity * item.price_at_add, 2),
        }
        for item in items
    ]