import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'
import crypto from 'crypto'
import { syncUserApiKeyAggregates } from '@/lib/execution-log-aggregates'

export async function GET() {
  const { userId } = await auth()
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    await syncUserApiKeyAggregates(userId)
  } catch (error) {
    console.error('[api/keys] aggregate sync error:', error)
    return NextResponse.json({ error: 'Failed to sync key totals' }, { status: 500 })
  }

  const { data, error } = await supabase
    .from('api_keys')
    .select('id, name, key_prefix, key_suffix, model, tags, requests, cost, total_savings, status, created_at, last_used')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })

  if (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }

  return NextResponse.json(data)
}

export async function POST(request: Request) {
  const { userId } = await auth()
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }
  const { name, model, tags } = body as { name: unknown; model: unknown; tags: unknown }

  if (typeof name !== 'string' || !name.trim() || typeof model !== 'string' || !model.trim()) {
    return NextResponse.json({ error: 'name and model are required' }, { status: 400 })
  }

  const raw = crypto.randomBytes(16).toString('hex') // 128-bit entropy
  const key = `sk_live_${raw}`

  const { data, error } = await supabase
    .from('api_keys')
    .insert({
      user_id: userId,
      name: (name as string).trim(),
      key,
      key_prefix: 'sk_live_',
      key_suffix: raw.slice(-4),
      model: (model as string).trim(),
      tags: Array.isArray(tags) ? tags : [],
    })
    .select('id, name, key_prefix, key_suffix, model, tags, requests, cost, status, created_at, last_used')
    .single()

  if (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }

  // Full key returned once only — never returned again after this
  return NextResponse.json({ ...data, key }, { status: 201 })
}
