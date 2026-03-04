import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

// NOTE: The frontend saves `model` (user-facing name from api_keys) while the Python
// ClassificationCategory schema expects `model_id` (provider model ID), `provider`,
// `endpoint`, and `request_defaults`. A mapping layer is needed before the inference
// engine can consume DB-backed configs directly.

const DEFAULT_CONFIG = {
  default_category_id: 'simple',
  categories: [
    { id: 'simple', name: 'Simple', description: '', model: '' },
    { id: 'complex', name: 'Complex', description: '', model: '' },
  ],
}

export async function GET() {
  const { userId } = await auth()
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { data, error } = await supabase
    .from('routing_configs')
    .select('config')
    .eq('user_id', userId)
    .single()

  // PGRST116 = no rows found (expected for new users)
  if (error && error.code !== 'PGRST116') {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }

  return NextResponse.json(data?.config ?? DEFAULT_CONFIG)
}

export async function PUT(request: Request) {
  const { userId } = await auth()
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const config = body as { default_category_id?: unknown; categories?: unknown }
  if (typeof config.default_category_id !== 'string' || !Array.isArray(config.categories)) {
    return NextResponse.json({ error: 'Invalid config structure' }, { status: 400 })
  }

  const categories = config.categories as unknown[]
  const validCategories = categories.every(
    (c) =>
      c !== null &&
      typeof c === 'object' &&
      typeof (c as Record<string, unknown>).id === 'string' &&
      typeof (c as Record<string, unknown>).name === 'string'
  )
  if (!validCategories) {
    return NextResponse.json({ error: 'Each category must have id and name' }, { status: 400 })
  }

  const categoryIds = (config.categories as { id: string }[]).map((c) => c.id)
  if (!categoryIds.includes(config.default_category_id as string)) {
    return NextResponse.json(
      { error: 'default_category_id must match a category id' },
      { status: 400 }
    )
  }

  const { error } = await supabase
    .from('routing_configs')
    .upsert(
      { user_id: userId, config: body, updated_at: new Date().toISOString() },
      { onConflict: 'user_id' }
    )

  if (error) return NextResponse.json({ error: 'Internal server error' }, { status: 500 })

  return NextResponse.json({ ok: true })
}
