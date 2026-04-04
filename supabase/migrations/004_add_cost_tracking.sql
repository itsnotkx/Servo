-- Add cost tracking to execution_logs
alter table execution_logs
    add column if not exists total_cost numeric(12,8) not null default 0;

-- Atomically add a cost increment to api_keys.cost
create or replace function increment_api_key_cost(p_key_id uuid, p_cost numeric)
returns void
language sql
as $$
    update api_keys set cost = cost + p_cost where id = p_key_id;
$$;
