select
    product_id,
    sku,
    product_name,
    lower(category) as category,
    list_price,
    _loaded_at
from {{ source('raw', 'products') }}