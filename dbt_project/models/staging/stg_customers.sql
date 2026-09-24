select
    customer_id,
    lower(email)                        as email,
    split_part(lower(email), '@', 2)    as email_domain,
    signup_date,
    upper(country)                      as country,
    _loaded_at
from {{ source('raw', 'customers') }}