import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

const DEFAULT_CONFIG = {
  default_category_id: 'simple',
  categories: [
    {
      id: 'simple',
      name: 'Simple',
      description:
        'Use for direct, bounded tasks: factual Q&A, concise explanations, and routine coding work (e.g. implementing a single function, small bug fixes). Prefer this category whenever the request can be fully handled without deep multi-step analysis.',
      model: '',
    },
    {
      id: 'complex',
      name: 'Complex',
      description:
        'Use only when the task genuinely requires deeper reasoning: broad system design, non-trivial architecture or migration plans, advanced debugging across multiple interacting components, or nuanced tradeoff analysis. Do not use for routine single-file or single-function tasks.',
      model: '',
    },
  ],
}

export async function GET() {
  const { userId } = await auth()
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { data } = await supabase
    .from('routing_configs')
    .select('config')
    .eq('user_id', userId)
    .single()

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

  const { error } = await supabase
    .from('routing_configs')
    .upsert(
      { user_id: userId, config: body, updated_at: new Date().toISOString() },
      { onConflict: 'user_id' }
    )

  if (error) return NextResponse.json({ error: 'Internal server error' }, { status: 500 })

  return NextResponse.json({ ok: true })
}
