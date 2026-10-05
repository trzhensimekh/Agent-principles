# Build an integer-cent quote library

Implement a Python 3.11+ standard-library module `pricing.py` exposing `quote(items, discount_percent=0, shipping_cents=0, tax_percent=0)`. Choose the internal architecture yourself. Write focused tests and a short README. No I/O, persistence, dependencies, currency conversion, or concurrency.

`items` is a nonempty list of dictionaries. Each has `sku` (nonempty string), `unit_price_cents` (nonnegative integer excluding bool), and `quantity` (positive integer excluding bool). Repeated SKUs and zero-price items are valid. Do not mutate caller inputs. Invalid input raises ValueError.

Discount and tax percentages are integers from 0 through 100 inclusive, excluding bool. Shipping is nonnegative integer cents excluding bool. Invalid arguments raise ValueError.

- subtotal = sum(unit_price_cents * quantity)
- discount = floor(subtotal * discount_percent / 100)
- shipping = shipping_cents
- tax = floor((subtotal - discount) * tax_percent / 100); shipping is not taxable
- total = subtotal - discount + shipping + tax

Return a dictionary containing `subtotal_cents`, `discount_cents`, `shipping_cents`, `tax_cents`, `total_cents`. All amounts are exact integers. Use integer arithmetic so very large amounts remain exact. Calls must be independent and deterministic. No additional public interface is required.
