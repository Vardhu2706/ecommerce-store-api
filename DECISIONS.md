# DECISIONS.md

## 1. Lazy Cart Creation

**Decision:** A cart is created only when the first item is added, not when a session starts.

**Rationale:** There is no concept of a session or user registration in this system. Creating a cart eagerly would require a separate "start session" endpoint with no clear trigger. Lazy creation keeps the surface area small: `POST /cart/items` is the single entry point, and an empty `GET /cart` response (`cart_id: null`) signals that no cart exists yet.

---

## 2. Admin-Gated Discount Approval

**Decision:** Discount codes are generated at approval time, not when the nth order triggers eligibility.

**Rationale:** Generating the code immediately at the nth order would mean codes exist before anyone has reviewed them. The admin approval step acts as a business gate — the operator decides whether to honour the discount. This also means a rejected discount never carries a usable code, which is cleaner than generating and then invalidating one.

---

## 3. Discount Code Scoped to User

**Decision:** Each discount belongs to a specific user; codes are not redeemable globally.

**Rationale:** A global code pool would require a redemption lookup and introduce race conditions under concurrent checkout. Scoping to `user_id` means the check during checkout is a simple filter on the user's own discounts, with no cross-user contention. It also makes audit trails clear: every discount has an unambiguous owner.

---

## 4. Checkout Fallback on Discount Conflict

**Decision:** If a discount becomes invalid between `/checkout/preview` and `/checkout/confirm` (e.g. used by a concurrent request), the order is placed without the discount rather than returning an error.

**Rationale:** Blocking the checkout would be a worse user experience than proceeding at full price — the user has already reviewed their cart and confirmed intent. The response clearly signals `discount_applied: false` so the client can inform the user. Since the store is in-memory with no true concurrency (GIL-protected), this is primarily a defensive design that mirrors real-world distributed system behaviour.

---

## 5. Price Snapshot on Cart Item

**Decision:** `price_at_add` is captured on `CartItem` at the moment the item is added to the cart.

**Rationale:** Product prices can change while a cart is active. Recalculating totals from the current product price at checkout would surprise users who added items at a different price. The snapshot ensures the price the user saw when adding is the price they pay, which is standard ecommerce behaviour.

---

## 6. Multiple Discounts Allowed, One Applied Per Checkout

**Decision:** Each eligible order (5th, 10th, 15th, etc.) creates its own pending discount entry, regardless of how many others are pending or approved. At checkout, only one approved discount is auto-applied.

**Rationale:** The alternative — one pending discount at a time — would silently discard rewards the user legitimately earned. If a user's 5th order discount is still pending admin approval when they place their 10th order, blocking the new entry means they lose that reward entirely with no visibility. Accumulating entries is more honest: the user earned them, the admin can reject extras via the approval flow. Stacking at checkout is prevented at the redemption layer — only one approved discount is applied per order — not at the creation layer, keeping the two concerns separate.

---

## 7. Revert Clears Generated Code

**Decision:** On revert, both `code` and `approved_at` are set to `None`, returning the discount to a clean `pending_approval` state.

**Rationale:** If the code were retained after a revert, a user could have a code in hand for a discount that is no longer approved. Clearing the code at revert prevents any use of a stale code and ensures that a fresh approval generates a fresh, auditable code with a new `approved_at` timestamp.

---

## 8. Unified `GET /orders` Endpoint (User + Admin)

**Decision:** A single `GET /orders` endpoint serves both users (`X-User-Id`) and admins (`X-Admin-Key`), rather than duplicating the endpoint under `/admin/orders` only.

**Rationale:** Users have a natural need to view their own order history. Forcing them through an admin route is semantically wrong and would require exposing the admin key to non-admin clients. The unified endpoint checks for X-Admin-Key first — returning all orders if valid — then falls back to X-User-Id for a user-scoped view, rejecting requests missing both with a 400. The trade-off is a slightly more complex route handler managing two authentication paths. In a larger system this would be two separate endpoints with proper role-based middleware, but for this scope the unified approach keeps the API surface small without sacrificing correctness.
