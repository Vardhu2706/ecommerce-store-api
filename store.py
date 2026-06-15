products: dict[str, dict] = {
    'prod_1': {
        'id': 'prod_1',
        'name': 'Wireless Headphones',
        'price': 79.99
    },
    'prod_2': {
        'id': 'prod_2',
        'name': 'Mechanical Keyboard',
        'price': 129.99
    },
    'prod_3': {
        'id': 'prod_3',
        'name': 'USB-C Hub',
        'price': 49.99
    },
    'prod_4': {
        'id': 'prod_4',
        'name': 'Webcam HD',
        'price': 89.99
    },
    'prod_5': {
        'id': 'prod_5',
        'name': 'Desk Lamp',
        'price': 34.99
    }
}


carts: dict[str, dict] = {}
active_carts: dict[str, str] = {}
orders: dict[str, dict] = {}
discounts: dict[str, dict] = {}
user_order_counts: dict[str, int] = {}