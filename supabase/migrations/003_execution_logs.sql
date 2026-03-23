-- execution_logs: one row per route_and_execute() call from the SDK
create table if not exists execution_logs (
    id                  uuid primary key default gen_random_uuid(),
    key_id              uuid references api_keys(id) on delete set null,
    user_id             text not null,
    created_at          timestamptz not null default now(),
    prompt_preview      text,
    subtask_count       integer not null default 0,
    total_latency_ms    integer,
    total_input_tokens  integer not null default 0,
    total_output_tokens integer not null default 0,
    chunks              jsonb not null default '[]'::jsonb,
    model_usage         jsonb not null default '{}'::jsonb
);

create index if not exists execution_logs_user_id_idx   on execution_logs(user_id);
create index if not exists execution_logs_key_id_idx    on execution_logs(key_id);
create index if not exists execution_logs_created_at_idx on execution_logs(created_at desc);

-- Helper: atomically increment api_keys.requests
create or replace function increment_api_key_requests(p_key_id uuid)
returns void
language sql
as $$
    update api_keys set requests = requests + 1 where id = p_key_id;
$$;
