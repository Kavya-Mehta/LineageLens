select
    order_id,
    count(*)        as payment_count,
    sum(amount)     as paid_amount,
    max(paid_at)    as last_paid_at
from {{ ref('stg_payments') }}
group by order_id