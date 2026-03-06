/**
 * AuditWorker — Queue processor for AgentxploiTor audit jobs
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 * Polls the job queue, dequeues pending jobs, calls EntityHex
 * Security Agent endpoint, bridges HexStrike WebSocket events
 * back to connected miniapp clients.
 *
 * Started by server.js alongside the Next.js server.
 * Runs as a singleton background process.
 *
 * Flow per job:
 * 1. Dequeue job (status: queued → in_progress)
 * 2. Load session context from memory layer (SimpleMem + Code-Voyager)
 * 3. POST to HexStrike /api/v1/agents/security/audit
 * 4. Connect to HexStrike WS /ws/{request_id}
 * 5. Bridge HexStrike events → miniapp WS clients
 * 6. On scan_complete → update job → store results
 */

import WebSocket from 'ws'

// ── Config ────────────────────────────────────────────────────────────────

const HEXSTRIKE_BASE = process.env.HEXSTRIKE_API_URL || 'http://localhost:8000'
const HEXSTRIKE_WS = process.env.HEXSTRIKE_WS_URL || 'ws://localhost:8000'
const POLL_INTERVAL_MS = 2000
const JOB_TIMEOUT_MS = 360_000  // 6 minutes max per job
const MAX_CONCURRENT_JOBS = 3

// ── Types ─────────────────────────────────────────────────────────────────

interface AuditJob {
  id: string
  targetUrl?: string
  contractAddress?: string
  githubUrl?: string
  targetType?: string
  auditType?: string
  scope?: string
  blockchain?: string
  priority?: string
  status: string
  paymentVerified?: boolean
  paymentTxHash?: string
  requestedByFid?: number
  walletAddress?: string
  createdAt: string
  updatedAt: string
  hexstrikeRequestId?: string
  findings?: any[]
  overallSeverity?: string
  confidenceScore?: number
  agentsUsed?: string[]
  toolsUsed?: string[]
  error?: string
}

interface HexStrikeEvent {
  event: string
  request_id: string
  timestamp: string
  data: Record<string, any>
}

// ── Job Store Interface ───────────────────────────────────────────────────
// Shared with server.js via module-level singleton

declare global {
  var __auditJobStore: Map<string, AuditJob> | undefined
  var __auditWsClients: Map<string, Set<WebSocket>> | undefined
}

function getJobStore(): Map<string, AuditJob> {
  if (!global.__auditJobStore) {
    global.__auditJobStore = new Map()
  }
  return global.__auditJobStore
}

function getWsClients(): Map<string, Set<WebSocket>> {
  if (!global.__auditWsClients) {
    global.__auditWsClients = new Map()
  }
  return global.__auditWsClients
}

// ── Worker State ──────────────────────────────────────────────────────────

const activeJobs = new Set<string>()  // job IDs currently being processed

// ── Main Worker Loop ──────────────────────────────────────────────────────

export function startAuditWorker(): void {
  console.log('[AuditWorker] Starting — polling every', POLL_INTERVAL_MS, 'ms')
  setInterval(pollQueue, POLL_INTERVAL_MS)
}

async function pollQueue(): Promise<void> {
  if (activeJobs.size >= MAX_CONCURRENT_JOBS) return

  const store = getJobStore()
  const queued = Array.from(store.values())
    .filter(j => j.status === 'queued' && !activeJobs.has(j.id))
    .sort((a, b) => {
      // Priority order: critical > high > medium > low
      const order = { critical: 0, high: 1, medium: 2, low: 3 }
      const ap = order[a.priority as keyof typeof order] ?? 2
      const bp = order[b.priority as keyof typeof order] ?? 2
      return ap !== bp ? ap - bp : a.createdAt.localeCompare(b.createdAt)
    })

  for (const job of queued) {
    if (activeJobs.size >= MAX_CONCURRENT_JOBS) break
    processJob(job).catch(err => {
      console.error('[AuditWorker] Job failed:', job.id, err)
      updateJob(job.id, { status: 'failed', error: String(err) })
      broadcastToClients(job.id, {
        event: 'error',
        request_id: job.id,
        timestamp: new Date().toISOString(),
        data: { message: String(err) },
      })
    }).finally(() => {
      activeJobs.delete(job.id)
    })
  }
}

// ── Job Processor ─────────────────────────────────────────────────────────

async function processJob(job: AuditJob): Promise<void> {
  activeJobs.add(job.id)
  console.log('[AuditWorker] Processing job:', job.id, 'type:', job.auditType)

  // Mark in_progress
  updateJob(job.id, { status: 'in_progress' })

  // Build HexStrike request payload
  const payload = buildHexStrikePayload(job)

  // POST to HexStrike Security Audit endpoint
  let hexstrikeRequestId: string
  try {
    const res = await fetchWithTimeout(
      `${HEXSTRIKE_BASE}/api/v1/agents/security/audit`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      },
      30_000
    )

    if (!res.ok) {
      const text = await res.text()
      throw new Error(`HexStrike API error ${res.status}: ${text}`)
    }

    const data = await res.json()
    hexstrikeRequestId = data.request_id

    updateJob(job.id, { hexstrikeRequestId })

    broadcastToClients(job.id, {
      event: 'progress',
      request_id: job.id,
      timestamp: new Date().toISOString(),
      data: {
        message: 'Analysis started. 19 agents coordinating...',
        percent: 10,
      },
    })
  } catch (err) {
    throw new Error(`Failed to start HexStrike analysis: ${err}`)
  }

  // Connect to HexStrike WebSocket and bridge events
  await bridgeHexStrikeWebSocket(job.id, hexstrikeRequestId)
}

// ── HexStrike WebSocket Bridge ────────────────────────────────────────────

function bridgeHexStrikeWebSocket(
  jobId: string,
  hexstrikeRequestId: string
): Promise<void> {
  return new Promise((resolve, reject) => {
    const wsUrl = `${HEXSTRIKE_WS}/ws/${hexstrikeRequestId}`
    console.log('[AuditWorker] Connecting to HexStrike WS:', wsUrl)

    const ws = new WebSocket(wsUrl)
    const timeout = setTimeout(() => {
      ws.close()
      reject(new Error('HexStrike WebSocket timeout after 6 minutes'))
    }, JOB_TIMEOUT_MS)

    ws.on('open', () => {
      console.log('[AuditWorker] HexStrike WS connected for job:', jobId)
    })

    ws.on('message', (raw: Buffer) => {
      try {
        const evt: HexStrikeEvent = JSON.parse(raw.toString())
        handleHexStrikeEvent(jobId, evt, ws, timeout, resolve, reject)
      } catch {
        // Non-JSON message — ignore
      }
    })

    ws.on('error', (err: Error) => {
      clearTimeout(timeout)
      reject(new Error(`HexStrike WS error: ${err.message}`))
    })

    ws.on('close', () => {
      clearTimeout(timeout)
      // If job not yet completed, mark as failed
      const job = getJobStore().get(jobId)
      if (job && !['completed', 'failed'].includes(job.status)) {
        reject(new Error('HexStrike WS closed unexpectedly'))
      } else {
        resolve()
      }
    })

    // Keep-alive ping every 25 seconds
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      } else {
        clearInterval(pingInterval)
      }
    }, 25_000)
  })
}

function handleHexStrikeEvent(
  jobId: string,
  evt: HexStrikeEvent,
  ws: WebSocket,
  timeout: NodeJS.Timeout,
  resolve: () => void,
  reject: (err: Error) => void
): void {
  // Bridge ALL HexStrike events directly to miniapp clients
  // Translate request_id to our job ID
  const bridgedEvt = { ...evt, request_id: jobId }
  broadcastToClients(jobId, bridgedEvt)

  switch (evt.event) {
    case 'scan_complete': {
      clearTimeout(timeout)
      ws.close()

      // Update job with final results
      updateJob(jobId, {
        status: 'completed',
        findings: evt.data.findings || [],
        overallSeverity: evt.data.overall_severity,
        confidenceScore: evt.data.confidence_score,
        agentsUsed: evt.data.agents_used || [],
        toolsUsed: evt.data.tools_used || [],
      })

      console.log(
        '[AuditWorker] Job completed:', jobId,
        '| Severity:', evt.data.overall_severity,
        '| Findings:', evt.data.finding_count
      )
      resolve()
      break
    }

    case 'error': {
      clearTimeout(timeout)
      ws.close()
      updateJob(jobId, {
        status: 'failed',
        error: evt.data.message || 'Analysis failed',
      })
      reject(new Error(evt.data.message || 'HexStrike analysis failed'))
      break
    }

    case 'finding': {
      // Accumulate findings in job as they stream in
      const job = getJobStore().get(jobId)
      if (job) {
        const findings = job.findings || []
        findings.push(evt.data)
        updateJob(jobId, { findings })
      }
      break
    }

    case 'agent_loaded':
    case 'progress':
    case 'warning':
      // Already bridged to clients above — no additional job state update needed
      break
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────

function buildHexStrikePayload(job: AuditJob): Record<string, any> {
  return {
    contract_address: job.contractAddress,
    blockchain: job.blockchain || detectChain(job.contractAddress),
    github_url: job.githubUrl,
    target_url: job.targetUrl,
    target_type: job.targetType || detectTargetType(job),
    audit_type: job.auditType || 'contract_basic',
    scan_type: job.auditType?.includes('deep') ? 'comprehensive' : 'basic',
    requested_by_fid: job.requestedByFid || 0,
    options: {
      include_exploits: job.auditType === 'contract_deep',
      deep_analysis: job.auditType === 'contract_deep' || job.auditType === 'full_stack',
    },
  }
}

function detectTargetType(job: AuditJob): string {
  if (job.contractAddress) {
    return job.contractAddress.startsWith('0x') ? 'contract_evm' : 'contract_solana'
  }
  if (job.githubUrl) return 'github_repo'
  if (job.targetUrl) return 'miniapp_url'
  return 'contract_evm'
}

function detectChain(address?: string): string {
  if (!address) return 'base'
  // Default to Base for EVM addresses in Farcaster ecosystem
  return 'base'
}

function updateJob(id: string, updates: Partial<AuditJob>): void {
  const store = getJobStore()
  const job = store.get(id)
  if (job) {
    store.set(id, {
      ...job,
      ...updates,
      updatedAt: new Date().toISOString(),
    })
  }
}

function broadcastToClients(jobId: string, event: HexStrikeEvent | object): void {
  const clients = getWsClients().get(jobId)
  if (!clients || clients.size === 0) return
  const payload = JSON.stringify(event)
  for (const client of clients) {
    if (client.readyState === WebSocket.OPEN) {
      try {
        client.send(payload)
      } catch {
        clients.delete(client)
      }
    }
  }
}

async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs: number
): Promise<Response> {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await fetch(url, { ...options, signal: controller.signal })
  } finally {
    clearTimeout(id)
  }
}
