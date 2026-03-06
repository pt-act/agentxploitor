/**
 * GET /api/intelligence/stats
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━
 * System-wide learning statistics for transparency display.
 * Powers the "AgentxploiTor has completed X audits and learned Y patterns" UI.
 *
 * Glass-box: the intelligence layer is never hidden.
 */

import { NextResponse } from 'next/server'

const PYTHON_API = process.env.HEXSTRIKE_API_URL || 'http://localhost:8000'

export async function GET() {
  try {
    // Fetch stats from Python memory layer via HexStrike API
    const res = await fetch(`${PYTHON_API}/api/v1/intelligence/stats`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      next: { revalidate: 60 }, // cache for 60s — stats don't need to be real-time
    })

    if (!res.ok) {
      // Return a graceful fallback — stats display is non-critical
      return NextResponse.json(
        {
          total_audits: 0,
          unique_targets: 0,
          patterns_learned: 0,
          active_sessions: 0,
          simplemem_available: false,
          code_voyager_available: false,
          error: 'Intelligence layer initialising',
        },
        { status: 200 }
      )
    }

    const stats = await res.json()
    return NextResponse.json(stats)
  } catch {
    // Never let a stats failure surface as an error to the user
    return NextResponse.json(
      {
        total_audits: 0,
        unique_targets: 0,
        patterns_learned: 0,
        active_sessions: 0,
        simplemem_available: false,
        code_voyager_available: false,
        error: 'Intelligence layer unavailable',
      },
      { status: 200 }
    )
  }
}
