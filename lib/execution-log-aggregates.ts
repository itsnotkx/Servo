import { supabase } from '@/lib/supabase'

export async function syncApiKeyAggregates(keyId: string) {
  const { data: logs, error: logsError } = await supabase
    .from('execution_logs')
    .select('id, total_cost, total_savings')
    .eq('key_id', keyId)

  if (logsError) {
    throw logsError
  }

  const requests = logs?.length ?? 0
  const cost = (logs ?? []).reduce((sum, log) => sum + Number(log.total_cost ?? 0), 0)
  const totalSavings = (logs ?? []).reduce((sum, log) => sum + Number(log.total_savings ?? 0), 0)

  const { error: updateError } = await supabase
    .from('api_keys')
    .update({
      requests,
      cost: Number(cost.toFixed(8)),
      total_savings: Number(totalSavings.toFixed(8)),
    })
    .eq('id', keyId)

  if (updateError) {
    throw updateError
  }
}

export async function syncUserApiKeyAggregates(userId: string) {
  const { data: keys, error: keysError } = await supabase
    .from('api_keys')
    .select('id')
    .eq('user_id', userId)

  if (keysError) {
    throw keysError
  }

  for (const key of keys ?? []) {
    await syncApiKeyAggregates(key.id)
  }
}
