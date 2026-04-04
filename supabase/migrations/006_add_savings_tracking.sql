-- Add savings tracking to execution_logs and api_keys
alter table execution_logs
    add column if not exists total_savings numeric(12,8) not null default 0;

alter table api_keys
    add column if not exists total_savings numeric(12,8) not null default 0;

-- Atomically add a savings increment to api_keys.total_savings
create or replace function increment_api_key_savings(p_key_id uuid, p_savings numeric)
returns void
language sql
as $$
    update api_keys set total_savings = total_savings + p_savings where id = p_key_id;
$$;
