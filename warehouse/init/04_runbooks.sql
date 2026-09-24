INSERT INTO meta.runbooks (title, body, tags) VALUES
('Nulls in order_items.unit_price after vendor price-feed sync',
 'The upstream price feed occasionally lands order_items rows before the product price sync completes, leaving unit_price NULL for that batch. Row counts look normal because the rows are present. Revenue is understated because SUM() skips NULLs. Check the null rate on stg_order_items.unit_price for the affected order_date. Fix is to re-run the price sync and then rebuild from staging.',
 ARRAY['order_items','nulls','revenue','price-feed']),

('Payments schema changes from the billing team',
 'The billing team ships columns to raw.payments without notice. Staging models use explicit column lists, so a new column is silently ignored rather than breaking the run. Symptom is a green pipeline and a wrong number. Compare meta.column_snapshot across the last two runs for raw.payments before assuming the logic is wrong.',
 ARRAY['payments','schema','revenue','silent']),

('Warehouse connection pool exhaustion during 06:00 window',
 'Between 06:00 and 06:30 the BI extract job holds connections and dbt runs can fail to acquire one. These failures are transient and affect whichever model happens to run in that window. They do not invalidate an earlier successful materialization.',
 ARRAY['transient','connection','06:00']),

('Late-arriving orders from the EU region',
 'EU orders land up to four hours after the US batch. Daily revenue for the current day is expected to be incomplete until 08:00 UTC. This is not an incident.',
 ARRAY['orders','late-arriving','eu','freshness']),

('Rebuilding marts after a staging fix',
 'After correcting a staging model, rebuild downstream with dbt build --select stg_model+ rather than a full run. A full run takes 40 minutes and is rarely necessary.',
 ARRAY['dbt','rebuild','operations']),

('dim_customers row count drops on the first of the month',
 'The customer export is truncated and reloaded monthly. On the 1st, dim_customers can briefly show a lower row count mid-load. Wait for the load to finish before investigating.',
 ARRAY['dim_customers','row-count','monthly']),

('Currency column is always USD',
 'raw.orders.currency exists but has only ever contained USD. Do not build conversion logic on it. It is reserved for a multi-currency rollout that has not shipped.',
 ARRAY['orders','currency']),

('Escalation policy for data incidents',
 'File a ticket with the specific model, run_id, and timestamp attached. If root cause is not determinable from available metadata, say so explicitly in the ticket rather than proposing a likely cause. A triaged ticket with honest gaps is more useful to on-call than a confident guess.',
 ARRAY['escalation','policy','oncall']);