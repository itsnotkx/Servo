import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function GET(request: Request) {
    // 1. Extract Bearer token
    const authHeader = request.headers.get('authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return NextResponse.json({ error: 'Missing or invalid authorization header' }, { status: 401 })
    }

    const key = authHeader.replace('Bearer ', '')

    // 2. Validate the API key
    const { data: apiKeyData, error: keyError } = await supabase
        .from('api_keys')
        .select('id, status')
        .eq('key', key)
        .single()

    if (keyError || !apiKeyData) {
        return NextResponse.json({ error: 'Invalid API key' }, { status: 401 })
    }

    if (apiKeyData.status !== 'active') {
        return NextResponse.json({ error: 'API key is inactive' }, { status: 403 })
    }

    // 3. Fetch all model pricing rows
    const { data: pricing, error: pricingError } = await supabase
        .from('model_pricing')
        .select('model_id, provider, input_per_million, output_per_million')

    if (pricingError) {
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
    }

    return NextResponse.json({ pricing: pricing ?? [] })
}
