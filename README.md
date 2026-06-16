# Ecommerce Store API

A FastAPI-based ecommerce backend with cart management, checkout, and an admin-controlled discount system. All state is held in-memory — no database required. The API is fully documented via Swagger UI at `/docs`.

---

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd ecommerce

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the development server
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

## Environment Variables

| Variable              | Default  | Description                                               |
|-----------------------|----------|-----------------------------------------------------------|
| `DISCOUNT_EVERY_N`    | `5`      | Every Nth order triggers a discount eligibility entry     |
| `DISCOUNT_PERCENTAGE` | `10.0`   | Percentage off applied when a discount is used            |
| `ADMIN_KEY`           | `secret` | Secret key required for all `/admin/*` routes             |

Set them before starting the server:

```bash
# Windows PowerShell
$env:DISCOUNT_EVERY_N = "3"
$env:ADMIN_KEY = "mysecretkey"

# macOS/Linux
export DISCOUNT_EVERY_N=3
export ADMIN_KEY=mysecretkey
```

---

## Running Tests

```bash
# From the ecommerce/ directory
pytest tests/
```

Tests cover only the service layer (`cart_service`, `checkout_service`, `discount_service`). The in-memory store is reset between every test via an `autouse` fixture.

---

## API Overview

### Products
| Method | Path        | Description       |
|--------|-------------|-------------------|
| GET    | `/products` | List all products |

### Cart  _(requires `X-User-Id` header)_
| Method | Path                          | Description                      |
|--------|-------------------------------|----------------------------------|
| GET    | `/cart`                       | View active cart                 |
| POST   | `/cart/items`                 | Add item (creates cart lazily)   |
| PATCH  | `/cart/items/{product_id}`    | Update item quantity             |
| DELETE | `/cart/items/{product_id}`    | Remove item                      |
| DELETE | `/cart`                       | Clear all items from cart        |

### Checkout  _(requires `X-User-Id` header)_
| Method | Path                 | Description                               |
|--------|----------------------|-------------------------------------------|
| GET    | `/checkout/preview`  | Preview total with any available discount |
| POST   | `/checkout/confirm`  | Place the order                           |

### Orders  _(requires `X-User-Id` or `X-Admin-Key` header)_
| Method | Path      | Description                                         |
|--------|-----------|-----------------------------------------------------|
| GET    | `/orders` | User's own orders, or all orders for admin          |

### Admin  _(requires `X-Admin-Key` header)_
| Method | Path                                    | Description                   |
|--------|-----------------------------------------|-------------------------------|
| GET    | `/admin/discounts`                      | List discounts (filterable)   |
| PATCH  | `/admin/discounts/{id}/approve`         | Approve and generate code     |
| PATCH  | `/admin/discounts/{id}/reject`          | Reject a pending discount     |
| PATCH  | `/admin/discounts/{id}/revert`          | Revert to pending             |
| GET    | `/admin/orders`                         | List all orders (filterable)  |
| GET    | `/admin/stats`                          | Aggregate revenue/discount stats |

---

## Design Decisions

Notable design and trade-off decisions (lazy cart creation, discount approval flow, checkout fallback behavior, etc.) are documented in [`DECISIONS.md`](./DECISIONS.md).

---

## Swagger UI

Run the server and open `http://localhost:8000/docs` for an interactive explorer where you can try every endpoint directly in the browser.

---

## Testing
Import `postman/Ecommerce Store API.json` into Postman.
Set the `base_url` environment variable to the live URL or http://localhost:8000.

---

## Live API
Deployed on Railway: [https://ecommerce-store-api-production.up.railway.app/docs](https://ecommerce-store-api-production.up.railway.app/docs)