create table routing_configs (
  id         uuid        primary key default gen_random_uuid(),
  user_id    text        not null unique,
  config     jsonb       not null,
  updated_at timestamptz not null default now()
);
