select
    order_id,
    customer_id,
    lower(order_status)     as order_status,
    ordered_at,
    ordered_at::date        as order_date,
    currency,
    _loaded_at
from {{ source('raw', 'orders') }}