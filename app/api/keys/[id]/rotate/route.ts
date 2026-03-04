import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'
import crypto from 'crypto'

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { userId } = await auth()
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { id } = await params

  const raw = crypto.randomBytes(16).toString('hex')
  const key = `sk_live_${raw}`

  const { data, error } = await supabase
    .from('api_keys')
    .update({
      key,
      key_prefix: 'sk_live_',
      key_suffix: raw.slice(-4),
    })
    .eq('id', id)
    .eq('user_id', userId) // scoped to user
    .select('id, name, key_prefix, key_suffix, model, tags, requests, cost, status, created_at, last_used')
    .single()

  if (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }

  // Full key returned once only
  return NextResponse.json({ ...data, key })
}
