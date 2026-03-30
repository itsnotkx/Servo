import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'
import { syncApiKeyAggregates } from '@/lib/execution-log-aggregates'

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
  const promptPreview = typeof body.prompt_preview === 'string' ? body.prompt_preview : null
  const logPayload = {
    key_id: keyRow.id,
    user_id: keyRow.user_id,
    prompt_preview: promptPreview,
    subtask_count: body.subtask_count ?? 0,
    total_latency_ms: body.total_latency_ms ?? null,
    total_input_tokens: body.total_input_tokens ?? 0,
    total_output_tokens: body.total_output_tokens ?? 0,
    total_cost: totalCost,
    total_savings: totalSavings,
    chunks: body.chunks ?? [],
    model_usage: body.model_usage ?? {},
  }

  // --- Write execution log ---
  let writeError: unknown = null

  if (promptPreview) {
    const { data: existingLog, error: lookupErr } = await supabase
      .from('execution_logs')
      .select('id')
      .eq('key_id', keyRow.id)
      .eq('prompt_preview', promptPreview)
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle()

    if (lookupErr) {
      console.error('[telemetry] lookup error:', lookupErr)
      return NextResponse.json({ error: 'Failed to write telemetry' }, { status: 500 })
    }

    if (existingLog) {
      const { error: updateErr } = await supabase
        .from('execution_logs')
        .update({
          ...logPayload,
          created_at: new Date().toISOString(),
        })
        .eq('id', existingLog.id)
      writeError = updateErr
    } else {
      const { error: insertErr } = await supabase
        .from('execution_logs')
        .insert(logPayload)
      writeError = insertErr
    }
  } else {
    const { error: insertErr } = await supabase
      .from('execution_logs')
      .insert(logPayload)
    writeError = insertErr
  }

  if (writeError) {
    console.error('[telemetry] write error:', writeError)
    return NextResponse.json({ error: 'Failed to write telemetry' }, { status: 500 })
  }

  try {
    await syncApiKeyAggregates(keyRow.id)
  } catch (aggregateError) {
    console.error('[telemetry] aggregate sync error:', aggregateError)
    return NextResponse.json({ error: 'Failed to update usage totals' }, { status: 500 })
  }

  return NextResponse.json({ ok: true }, { status: 201 })
}
