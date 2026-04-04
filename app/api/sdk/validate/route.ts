import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function POST(request: Request) {
  const authHeader = request.headers.get('authorization')
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Missing or invalid authorization header' }, { status: 401 })
  }

  const key = authHeader.replace('Bearer ', '')

  // 1. Look up the key in the database
  const { data, error } = await supabase
    .from('api_keys')
    .select('id, user_id, model, tags, status')
    .eq('key', key)
    .single()

  if (error || !data) {
    return NextResponse.json({ error: 'Invalid API key' }, { status: 401 })
  }

  // 2. Check if the key is active
  if (data.status !== 'active') {
    return NextResponse.json({ error: 'API key is inactive' }, { status: 403 })
  }

  // 3. Update last_used
  await supabase
    .from('api_keys')
    .update({ last_used: new Date().toISOString() })
    .eq('id', data.id)

  // 4. Fetch tiers for the user
  // For now, we'll return a static tiers mapping as a placeholder 
  // until we have a more robust way to fetch user-specific tiers.
  // In the future, this could hit the inference backend or a database table.
  const tiers = {
    simple: 'gemini-2.5-flash-lite',
    complex: 'gemini-2.5-flash'
  }

  return NextResponse.json({
    valid: true,
    key_id: data.id,
    user_id: data.user_id,
    model: data.model,
    tags: data.tags,
    tiers: tiers
  })
}
