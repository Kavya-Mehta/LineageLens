CREATE TABLE raw.customers (
  customer_id   INTEGER PRIMARY KEY,
  email         TEXT        NOT NULL,
  signup_date   DATE        NOT NULL,
  country       TEXT        NOT NULL,
  _loaded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE raw.products (
  product_id    INTEGER PRIMARY KEY,
  sku           TEXT        NOT NULL,
  product_name  TEXT        NOT NULL,
  category      TEXT        NOT NULL,
  list_price    NUMERIC(10,2) NOT NULL,
  _loaded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE raw.orders (
  order_id      INTEGER PRIMARY KEY,
  customer_id   INTEGER     NOT NULL REFERENCES raw.customers(customer_id),
  order_status  TEXT        NOT NULL,
  ordered_at    TIMESTAMPTZ NOT NULL,
  currency      TEXT        NOT NULL DEFAULT 'USD',
  _loaded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE raw.order_items (
  order_item_id INTEGER PRIMARY KEY,
  order_id      INTEGER     NOT NULL REFERENCES raw.orders(order_id),
  product_id    INTEGER     NOT NULL REFERENCES raw.products(product_id),
  quantity      INTEGER     NOT NULL,
  unit_price    NUMERIC(10,2),
  _loaded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE raw.payments (
  payment_id    INTEGER PRIMARY KEY,
  order_id      INTEGER     NOT NULL REFERENCES raw.orders(order_id),
  amount        NUMERIC(10,2) NOT NULL,
  method        TEXT        NOT NULL,
  paid_at       TIMESTAMPTZ NOT NULL,
  _loaded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON raw.orders (ordered_at);
CREATE INDEX ON raw.order_items (order_id);
CREATE INDEX ON raw.payments (order_id);
