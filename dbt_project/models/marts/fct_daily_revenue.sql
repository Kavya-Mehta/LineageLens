-- This is the dashboard number. When someone says "revenue looks wrong",
-- they are looking at a chart built on this table.
select
    order_date,
    count(*)                                                        as orders,
    count(*) filter (where order_status = 'completed')              as completed_orders,
    sum(gross_amount) filter (where order_status = 'completed')     as gross_revenue,
    sum(paid_amount)  filter (where order_status = 'completed')     as paid_revenue
from {{ ref('fct_orders') }}
group by order_date