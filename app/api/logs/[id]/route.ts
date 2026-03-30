import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'
import { syncApiKeyAggregates } from '@/lib/execution-log-aggregates'

type RouteContext = {
  params: Promise<{ id: string }>
}

export async function DELETE(_request: Request, context: RouteContext) {
  const { userId } = await auth()
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { id } = await context.params

  const { data: existingLog, error: lookupError } = await supabase
    .from('execution_logs')
    .select('id, key_id')
    .eq('id', id)
    .eq('user_id', userId)
    .maybeSingle()

  if (lookupError) {
    return NextResponse.json({ error: 'Failed to load log' }, { status: 500 })
  }

  if (!existingLog) {
    return NextResponse.json({ error: 'Log not found' }, { status: 404 })
  }

  const { error } = await supabase
    .from('execution_logs')
    .delete()
    .eq('id', existingLog.id)
    .eq('user_id', userId)

  if (error) {
    return NextResponse.json({ error: 'Failed to delete log' }, { status: 500 })
  }

  if (existingLog.key_id) {
    try {
      await syncApiKeyAggregates(existingLog.key_id)
    } catch {
      return NextResponse.json({ error: 'Failed to update usage totals' }, { status: 500 })
    }
  }

  return NextResponse.json({ ok: true })
}
