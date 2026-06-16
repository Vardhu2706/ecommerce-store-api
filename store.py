from models.cart import Cart
from models.discount import Discount
from models.order import Order
from models.product import Product


products: dict[str, Product] = {
    "prod_1": Product(id="prod_1", name="Wireless Headphones", price=79.99),
    "prod_2": Product(id="prod_2", name="Mechanical Keyboard", price=129.99),
    "prod_3": Product(id="prod_3", name="USB-C Hub", price=49.99),
    "prod_4": Product(id="prod_4", name="Webcam HD", price=89.99),
    "prod_5": Product(id="prod_5", name="Desk Lamp", price=34.99),
}


carts: dict[str, Cart] = {}
active_carts: dict[str, str] = {}
orders: dict[str, Order] = {}
discounts: dict[str, Discount] = {}
user_order_counts: dict[str, int] = {}