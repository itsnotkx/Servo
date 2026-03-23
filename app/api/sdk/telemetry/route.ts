import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function POST(request: Request) {
  // --- Auth: Bearer token ---
  const authHeader = request.headers.get('authorization')
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Missing or invalid authorization header' }, { status: 401 })
  }
  const key = authHeader.replace('Bearer ', '')

  const { data: keyRow, error: keyErr } = await supabase
    .from('api_keys')
    .select('id, user_id, status')
    .eq('key', key)
    .single()

  if (keyErr || !keyRow) {
    return NextResponse.json({ error: 'Invalid API key' }, { status: 401 })
  }
  if (keyRow.status !== 'active') {
    return NextResponse.json({ error: 'API key is inactive' }, { status: 403 })
  }

  // --- Parse body ---
  let body: Record<string, unknown>
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const totalCost: number = typeof body.total_cost === 'number' ? body.total_cost : 0
  const totalSavings: number = typeof body.total_savings === 'number' ? body.total_savings : 0

  // --- Write execution log ---
  const { error: insertErr } = await supabase.from('execution_logs').insert({
    key_id: keyRow.id,
    user_id: keyRow.user_id,
    prompt_preview: body.prompt_preview ?? null,
    subtask_count: body.subtask_count ?? 0,
    total_latency_ms: body.total_latency_ms ?? null,
    total_input_tokens: body.total_input_tokens ?? 0,
    total_output_tokens: body.total_output_tokens ?? 0,
    total_cost: totalCost,
    total_savings: totalSavings,
    chunks: body.chunks ?? [],
    model_usage: body.model_usage ?? {},
  })

  if (insertErr) {
    console.error('[telemetry] insert error:', insertErr)
    return NextResponse.json({ error: 'Failed to write telemetry' }, { status: 500 })
  }

  // --- Atomically increment api_keys.requests, cost, and savings ---
  await supabase.rpc('increment_api_key_requests', { p_key_id: keyRow.id })
  if (totalCost > 0) {
    await supabase.rpc('increment_api_key_cost', { p_key_id: keyRow.id, p_cost: totalCost })
  }
  if (totalSavings > 0) {
    await supabase.rpc('increment_api_key_savings', { p_key_id: keyRow.id, p_savings: totalSavings })
  }

  return NextResponse.json({ ok: true }, { status: 201 })
}
