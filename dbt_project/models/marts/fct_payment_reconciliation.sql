select
    order_id,
    order_date,
    gross_amount,
    paid_amount,
    coalesce(paid_amount, 0) - coalesce(gross_amount, 0) as variance,
    case
        when paid_amount is null then 'unpaid'
        when abs(coalesce(paid_amount, 0) - coalesce(gross_amount, 0)) < 0.01 then 'matched'
        else 'variance'
    end as reconciliation_status
from {{ ref('fct_orders') }}