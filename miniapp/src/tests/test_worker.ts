/**
 * Group 1 Tests — Queue Worker + WebSocket Bridge
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 * T1.1: Worker picks up queued job and calls HexStrike (mock)
 * T1.2: Worker correctly updates job status through lifecycle
 * T1.3: WebSocket bridge forwards HexStrike events to correct client
 * T1.4: Worker handles HexStrike unavailable gracefully
 *
 * Run: npx vitest run src/tests/test_worker.ts
 */

import { describe, it, expect, vi } from 'vitest'
import WS from 'ws'
const { WebSocketServer } = WS
const WebSocket = WS
import { createServer } from 'http'

// ── Mock HexStrike Server ─────────────────────────────────────────────────

function createMockHexStrikeServer(port: number, scenario: 'success' | 'error' | 'unavailable') {
  if (scenario === 'unavailable') return null

  const server = createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/api/v1/agents/security/audit') {
      res.writeHead(200, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({
        status: 'queued',
        request_id: 'mock-request-123',
        websocket_url: `ws://localhost:${port}/ws/mock-request-123`,
        estimated_time: 30,
      }))
    }
  })

  const wss = new WebSocketServer({ server, path: '/ws/mock-request-123' })

  wss.on('connection', (ws) => {
    // Simulate HexStrike event stream
    setTimeout(() => {
      ws.send(JSON.stringify({
        event: 'agent_loaded',
        request_id: 'mock-request-123',
        timestamp: new Date().toISOString(),
        data: { agent: 'IntelligentDecisionEngine', message: 'Agent ready' },
      }))
    }, 50)

    setTimeout(() => {
      ws.send(JSON.stringify({
        event: 'finding',
        request_id: 'mock-request-123',
        timestamp: new Date().toISOString(),
        data: {
          severity: 'critical',
          title: 'Reentrancy vulnerability',
          description: 'withdraw() is vulnerable to reentrancy',
          location: 'Vault.sol:142',
          confidence: 0.96,
        },
      }))
    }, 100)

    const finalEvent = scenario === 'error'
      ? { event: 'error', data: { message: 'Analysis failed' } }
      : {
          event: 'scan_complete',
          data: {
            overall_severity: 'critical',
            finding_count: 1,
            confidence_score: 0.96,
            agents_used: ['IntelligentDecisionEngine', 'CVEIntelligenceManager'],
            tools_used: ['slither'],
            message: 'Analysis complete.',
          },
        }

    setTimeout(() => {
      ws.send(JSON.stringify({
        ...finalEvent,
        request_id: 'mock-request-123',
        timestamp: new Date().toISOString(),
      }))
      ws.close()
    }, 200)
  })

  return new Promise<() => void>((resolve) => {
    server.listen(port, () => {
      resolve(() => {
        wss.close()
        server.close()
      })
    })
  })
}

// ── Test Helpers ──────────────────────────────────────────────────────────

function makeJob(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    id: `job-${Math.random().toString(36).slice(2, 8)}`,
    contractAddress: '0xabcdef1234567890abcdef1234567890abcdef12',
    targetType: 'contract_evm',
    auditType: 'contract_deep',
    blockchain: 'base',
    priority: 'high',
    status: 'queued',
    requestedByFid: 12345,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    findings: [],
    ...overrides,
  }
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe('Group 1: Queue Worker + WebSocket Bridge', () => {

  // T1.1: Worker picks up queued job and calls HexStrike
  it('T1.1: calls HexStrike Security Audit endpoint for queued job', async () => {
    const MOCK_PORT = 18001
    const cleanup = await createMockHexStrikeServer(MOCK_PORT, 'success') as () => void

    const calls: string[] = []
    const originalFetch = global.fetch
    global.fetch = vi.fn(async (url: string, opts: RequestInit) => {
      calls.push(url)
      // Proxy to mock server
      return originalFetch(
        url.replace('http://localhost:8000', `http://localhost:${MOCK_PORT}`),
        opts
      )
    }) as unknown as typeof global.fetch

    try {
      // Import worker with mock URL
      process.env.HEXSTRIKE_API_URL = `http://localhost:${MOCK_PORT}`
      process.env.HEXSTRIKE_WS_URL = `ws://localhost:${MOCK_PORT}`

      const { startAuditWorker } = await import('./audit-worker')

      // Setup global job store
      const job = makeJob()
      global.__auditJobStore = new Map([[job.id, job]])
      global.__auditWsClients = new Map()

      // Trigger one poll cycle
      // (processJob is called internally by pollQueue)
      // We test the HexStrike call was made
      const callMade = new Promise<void>((resolve) => {
        const check = setInterval(() => {
          if (calls.some(c => c.includes('/api/v1/agents/security/audit'))) {
            clearInterval(check)
            resolve()
          }
        }, 50)
        setTimeout(() => { clearInterval(check); resolve() }, 5000)
      })

      startAuditWorker()
      await callMade

      expect(calls.some(c => c.includes('/api/v1/agents/security/audit'))).toBe(true)
    } finally {
      global.fetch = originalFetch
      cleanup?.()
    }
  }, 10_000)

  // T1.2: Worker updates job status through lifecycle
  it('T1.2: job transitions queued → in_progress → completed', async () => {
    const MOCK_PORT = 18002
    const cleanup = await createMockHexStrikeServer(MOCK_PORT, 'success') as () => void

    process.env.HEXSTRIKE_API_URL = `http://localhost:${MOCK_PORT}`
    process.env.HEXSTRIKE_WS_URL = `ws://localhost:${MOCK_PORT}`

    const job = makeJob()
    const store = new Map([[job.id, job]])
    global.__auditJobStore = store
    global.__auditWsClients = new Map()

    try {
      // Dynamically import to get fresh module with mock env
      const { startAuditWorker } = await import('./audit-worker?v=2')

      startAuditWorker()

      // Wait for job to complete (mock server sends scan_complete after 200ms)
      await new Promise<void>((resolve) => {
        const check = setInterval(() => {
          const current = store.get(job.id)
          if (current?.status === 'completed') {
            clearInterval(check)
            resolve()
          }
        }, 100)
        setTimeout(() => { clearInterval(check); resolve() }, 8000)
      })

      const completed = store.get(job.id)
      expect(completed?.status).toBe('completed')
      expect(completed?.overallSeverity).toBe('critical')
      expect(completed?.findings?.length).toBeGreaterThan(0)
    } finally {
      cleanup?.()
    }
  }, 15_000)

  // T1.3: WebSocket bridge forwards HexStrike events to miniapp client
  it('T1.3: HexStrike events bridged to miniapp WS clients by job ID', async () => {
    const MOCK_PORT = 18003
    const cleanup = await createMockHexStrikeServer(MOCK_PORT, 'success') as () => void

    const job = makeJob()
    global.__auditJobStore = new Map([[job.id, job]])

    const receivedEvents: string[] = []

    // Create a mock miniapp client WebSocket
    const mockClient = {
      readyState: WebSocket.OPEN,
      send: vi.fn((data: string) => {
        const evt = JSON.parse(data)
        receivedEvents.push(evt.event)
      }),
    } as unknown as WebSocket

    // Register mock client for this job
    global.__auditWsClients = new Map([[job.id, new Set([mockClient])]])

    process.env.HEXSTRIKE_API_URL = `http://localhost:${MOCK_PORT}`
    process.env.HEXSTRIKE_WS_URL = `ws://localhost:${MOCK_PORT}`

    try {
      const { startAuditWorker } = await import('./audit-worker?v=3')
      startAuditWorker()

      // Wait for scan_complete to be bridged
      await new Promise<void>((resolve) => {
        const check = setInterval(() => {
          if (receivedEvents.includes('scan_complete')) {
            clearInterval(check)
            resolve()
          }
        }, 100)
        setTimeout(() => { clearInterval(check); resolve() }, 8000)
      })

      expect(receivedEvents).toContain('agent_loaded')
      expect(receivedEvents).toContain('finding')
      expect(receivedEvents).toContain('scan_complete')
      // All events must have our job ID, not HexStrike's request ID
      expect(mockClient.send).toHaveBeenCalledWith(
        expect.stringContaining(job.id)
      )
    } finally {
      cleanup?.()
    }
  }, 15_000)

  // T1.4: Worker handles HexStrike unavailable gracefully
  it('T1.4: job marked failed gracefully when HexStrike is unavailable', async () => {
    process.env.HEXSTRIKE_API_URL = 'http://localhost:19999' // nothing running here
    process.env.HEXSTRIKE_WS_URL = 'ws://localhost:19999'

    const job = makeJob()
    const store = new Map([[job.id, job]])
    global.__auditJobStore = store
    global.__auditWsClients = new Map([[job.id, new Set()]])

    const { startAuditWorker } = await import('./audit-worker?v=4')
    startAuditWorker()

    // Wait for job to fail
    await new Promise<void>((resolve) => {
      const check = setInterval(() => {
        const current = store.get(job.id)
        if (current?.status === 'failed') {
          clearInterval(check)
          resolve()
        }
      }, 100)
      setTimeout(() => { clearInterval(check); resolve() }, 8000)
    })

    const failed = store.get(job.id)
    expect(failed?.status).toBe('failed')
    expect(failed?.error).toBeTruthy()
    // Error message should be informative, not a raw crash
    expect(failed?.error).toContain('HexStrike')
  }, 15_000)
})
