select
    customer_id,
    min(order_date)                                                     as first_order_date,
    max(order_date)                                                     as last_order_date,
    count(*)                                                            as order_count,
    sum(case when order_status = 'completed' then gross_amount end)     as lifetime_gross
from {{ ref('int_order_totals') }}
group by customer_id