# Add selective discounts and tax exemptions

Extend the existing quote library while preserving all initial behavior and validations for callers who omit new arguments. Read the source and tests yourself; no previous agent conversation is available. Add regression tests and update the README.

Extend signature to `quote(items, discount_percent=0, shipping_cents=0, tax_percent=0, discount_cap_cents=None, shipping_taxable=False)`.

Each item optionally contains `discountable` and `taxable`, both booleans defaulting to True. Other types, including integers 0 and 1, are invalid. `shipping_taxable` must be bool. `discount_cap_cents` is None or a nonnegative integer excluding bool. Invalid input raises ValueError, and caller data must never be modified.

Compute each row subtotal as before. Eligible subtotal includes only discountable rows. Nominal discount is floor(eligible_subtotal * discount_percent / 100); cap it at discount_cap_cents when supplied. With zero eligible subtotal the discount is zero.

Allocate the total discount to discountable rows proportionally to their subtotals using integer largest remainders: each eligible row gets floor(total_discount * row_subtotal / eligible_subtotal), then remaining cents go to rows with the largest fractional remainders; ties are resolved in original input order. Non-discountable rows get zero. Allocation must sum exactly to total discount and never exceed any row subtotal. Zero-price rows must work without division errors.

Tax base is the sum of (row_subtotal - allocated_discount) for taxable rows, plus shipping when shipping_taxable is True. Compute tax once as floor(tax_base * tax_percent / 100). Total is subtotal - discount + shipping + tax.

Preserve all five existing output fields. Add `lines`, a list in input order of dictionaries with `sku`, `subtotal_cents`, `discount_cents`, `net_cents`, `taxable`. Do not round tax per line. Repeated SKUs remain separate rows. Very large amounts must remain exact. All defaults reproduce initial monetary outputs.
