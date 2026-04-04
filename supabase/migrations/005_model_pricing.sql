create table model_pricing (
  model_id           text  primary key,
  provider           text  not null,
  input_per_million  float not null,
  output_per_million float not null
);

-- MVP seed data (prices in USD per 1M tokens, as of March 2026)
insert into model_pricing (model_id, provider, input_per_million, output_per_million) values
  -- Google
  ('gemini-2.5-pro',      'google',    1.25,  10.00),
  ('gemini-2.5-flash',    'google',    0.15,   0.60),
  ('gemini-2.0-flash',    'google',    0.10,   0.40),
  ('gemini-1.5-pro',      'google',    1.25,   5.00),
  ('gemini-1.5-flash',    'google',    0.075,  0.30),
  ('gemini-1.0-pro',      'google',    0.50,   1.50),
  ('gemma-3-27b-it',      'google',    0.10,   0.20),
  ('gemma-3-12b-it',      'google',    0.05,   0.10),
  -- Anthropic
  ('claude-opus-4-5',     'anthropic', 15.00,  75.00),
  ('claude-opus-4.5',     'anthropic', 15.00,  75.00),
  ('claude-sonnet-4-5',   'anthropic',  3.00,  15.00),
  ('claude-sonnet-4.5',   'anthropic',  3.00,  15.00),
  ('claude-haiku-4-5',    'anthropic',  0.80,   4.00),
  ('claude-haiku-4.5',    'anthropic',  0.80,   4.00),
  -- OpenAI
  ('gpt-4o',              'openai',     2.50,  10.00),
  ('gpt-4o-mini',         'openai',     0.15,   0.60),
  ('gpt-4-turbo',         'openai',    10.00,  30.00),
  ('gpt-4',               'openai',    30.00,  60.00),
  ('gpt-3.5-turbo',       'openai',     0.50,   1.50);
