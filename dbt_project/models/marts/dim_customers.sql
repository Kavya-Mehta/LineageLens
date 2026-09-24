select
    c.customer_id,
    c.email_domain,
    c.country,
    c.signup_date,
    co.first_order_date,
    co.last_order_date,
    coalesce(co.order_count, 0) as order_count,
    co.lifetime_gross
from {{ ref('stg_customers') }} c
left join {{ ref('int_customer_orders') }} co on co.customer_id = c.customer_id