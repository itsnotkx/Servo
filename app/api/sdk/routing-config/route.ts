import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

const DEFAULT_CONFIG = {
    default_category_id: 'simple',
    categories: [
        { id: 'simple', name: 'Simple', description: '', model: '' },
        { id: 'complex', name: 'Complex', description: '', model: '' },
    ],
}

export async function GET(request: Request) {
    // 1. Extract Bearer token
    const authHeader = request.headers.get('authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return NextResponse.json({ error: 'Missing or invalid authorization header' }, { status: 401 })
    }

    const key = authHeader.replace('Bearer ', '')

    // 2. Look up the API key to get user_id
    const { data: apiKeyData, error: keyError } = await supabase
        .from('api_keys')
        .select('id, user_id, status')
        .eq('key', key)
        .single()

    if (keyError || !apiKeyData) {
        return NextResponse.json({ error: 'Invalid API key' }, { status: 401 })
    }

    // 3. Check if the key is active
    if (apiKeyData.status !== 'active') {
        return NextResponse.json({ error: 'API key is inactive' }, { status: 403 })
    }

    // 4. Fetch the routing config for this user
    const { data: routingData, error: routingError } = await supabase
        .from('routing_configs')
        .select('config')
        .eq('user_id', apiKeyData.user_id)
        .single()

    // PGRST116 = no rows found (expected for new users)
    if (routingError && routingError.code !== 'PGRST116') {
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
    }

    return NextResponse.json(routingData?.config ?? DEFAULT_CONFIG)
}
