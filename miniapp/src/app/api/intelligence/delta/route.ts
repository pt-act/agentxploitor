/**
 * POST /api/intelligence/delta
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━
 * Compare findings between two audit versions of the same target.
 * Powers the monitoring report: "These findings are NEW since your last audit."
 *
 * Body: { target_id, hash_a, hash_b }
 */

import { NextRequest, NextResponse } from 'next/server'

const PYTHON_API = process.env.HEXSTRIKE_API_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  let body: { target_id?: string; hash_a?: string; hash_b?: string }

  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const { target_id, hash_a, hash_b } = body

  if (!target_id || !hash_a || !hash_b) {
    return NextResponse.json(
      { error: 'target_id, hash_a and hash_b are required' },
      { status: 400 }
    )
  }

  try {
    const res = await fetch(`${PYTHON_API}/api/v1/intelligence/delta`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_id, hash_a, hash_b }),
    })

    if (!res.ok) {
      return NextResponse.json(
        { error: 'Delta analysis unavailable' },
        { status: 502 }
      )
    }

    const delta = await res.json()
    return NextResponse.json(delta)
  } catch {
    return NextResponse.json(
      { error: 'Delta analysis failed' },
      { status: 500 }
    )
  }
}
