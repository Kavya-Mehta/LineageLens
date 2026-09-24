select
    payment_id,
    order_id,
    amount,
    method,
    paid_at,
    _loaded_at
from {{ source('raw', 'payments') }}