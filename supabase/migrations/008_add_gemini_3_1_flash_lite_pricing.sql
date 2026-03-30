-- Add gemini-3.1-flash-lite pricing for the updated default routing pair.
-- Project assumption: retain the existing 3.1 preview pricing used by the SDK demo/tests.
insert into model_pricing (model_id, provider, input_per_million, output_per_million)
values ('gemini-3.1-flash-lite', 'google', 0.10, 0.40)
on conflict (model_id) do update
set
  provider = excluded.provider,
  input_per_million = excluded.input_per_million,
  output_per_million = excluded.output_per_million;
