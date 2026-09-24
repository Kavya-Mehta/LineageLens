with items as (
    select
        order_id,
        count(*)            as item_count,
        sum(line_amount)    as gross_amount
    from {{ ref('stg_order_items') }}
    group by order_id
)
select
    o.order_id,
    o.customer_id,
    o.order_date,
    o.ordered_at,
    o.order_status,
    coalesce(i.item_count, 0) as item_count,
    i.gross_amount
from {{ ref('stg_orders') }} o
left join items i on i.order_id = o.order_id