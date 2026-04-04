-- Add gemini-2.5-flash-lite pricing (missing from initial seed)
insert into model_pricing (model_id, provider, input_per_million, output_per_million)
values ('gemini-2.5-flash-lite', 'google', 0.10, 0.40)
on conflict (model_id) do update
  set input_per_million  = excluded.input_per_million,
      output_per_million = excluded.output_per_million;
