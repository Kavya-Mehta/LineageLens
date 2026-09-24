select
    t.order_id,
    t.customer_id,
    t.order_date,
    t.ordered_at,
    t.order_status,
    t.item_count,
    t.gross_amount,
    p.paid_amount,
    p.payment_count,
    p.last_paid_at
from {{ ref('int_order_totals') }} t
left join {{ ref('int_payments_by_order') }} p on p.order_id = t.order_id