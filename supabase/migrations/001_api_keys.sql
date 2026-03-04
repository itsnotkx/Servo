create table if not exists api_keys (
  id          uuid primary key default gen_random_uuid(),
  user_id     text not null,
  name        text not null,
  key         text not null unique,
  key_prefix  text not null,
  key_suffix  text not null,
  model       text not null,
  tags        text[] not null default '{}',
  requests    integer not null default 0,
  cost        numeric(10,4) not null default 0,
  status      text not null default 'active' check (status in ('active', 'inactive')),
  created_at  timestamptz not null default now(),
  last_used   timestamptz
);

create index if not exists api_keys_user_id_idx on api_keys (user_id);
create index if not exists api_keys_key_idx on api_keys (key);
