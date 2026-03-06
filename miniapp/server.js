/**
 * AgentxploiTor Miniapp Server
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━
 * Starts Next.js + WebSocket server + Audit Worker.
 *
 * WebSocket bridge: /api/ws/audit/{auditId}
 * Real HexStrike events flow from audit-worker.ts → here → miniapp client.
 * Mock reasoning stream removed — replaced with live HexStrike event bridge.
 */

const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');
const { WebSocketServer } = require('ws');

const dev = process.env.NODE_ENV !== 'production';
const hostname = 'localhost';
const port = parseInt(process.env.PORT || '3000', 10);

const app = next({ dev, hostname, port });
const handle = app.getRequestHandler();

// ── Shared global stores (shared with audit-worker.ts) ────────────────────
// Job store: auditId → job object
global.__auditJobStore = global.__auditJobStore || new Map();
// WS clients: auditId → Set<WebSocket>
global.__auditWsClients = global.__auditWsClients || new Map();

function setupWebSocketServer(server) {
  const wss = new WebSocketServer({ server, path: '/api/ws/audit' });

  wss.on('connection', (ws, req) => {
    const url = parse(req.url, true);
    const pathParts = url.pathname?.split('/').filter(Boolean) || [];

    // Path: /api/ws/audit/{auditId}
    if (
      pathParts[0] === 'api' &&
      pathParts[1] === 'ws' &&
      pathParts[2] === 'audit' &&
      pathParts[3]
    ) {
      const auditId = pathParts[3];

      // Register client for this audit job
      if (!global.__auditWsClients.has(auditId)) {
        global.__auditWsClients.set(auditId, new Set());
      }
      global.__auditWsClients.get(auditId).add(ws);

      // Send current job state immediately on connect
      const job = global.__auditJobStore.get(auditId);
      if (job) {
        ws.send(JSON.stringify({
          event: 'progress',
          request_id: auditId,
          timestamp: new Date().toISOString(),
          data: {
            message: `Connected. Current status: ${job.status}`,
            percent: { queued: 10, in_progress: 50, completed: 100 }[job.status] || 0,
          },
        }));

        // If already completed, send full results immediately
        if (job.status === 'completed') {
          ws.send(JSON.stringify({
            event: 'scan_complete',
            request_id: auditId,
            timestamp: new Date().toISOString(),
            data: {
              overall_severity: job.overallSeverity,
              finding_count: job.findings?.length || 0,
              confidence_score: job.confidenceScore,
              agents_used: job.agentsUsed || [],
              message: 'Analysis complete.',
            },
          }));
        }
      } else {
        ws.send(JSON.stringify({
          event: 'progress',
          request_id: auditId,
          timestamp: new Date().toISOString(),
          data: { message: 'Connected. Waiting for audit to start...', percent: 0 },
        }));
      }

      // Handle client messages
      ws.on('message', (message) => {
        try {
          const data = JSON.parse(message.toString());

          if (data.type === 'subscribe' && data.auditId && data.auditId !== auditId) {
            // Switch subscription to different audit
            const newId = data.auditId;
            if (!global.__auditWsClients.has(newId)) {
              global.__auditWsClients.set(newId, new Set());
            }
            global.__auditWsClients.get(newId).add(ws);
          }

          if (data.type === 'ping') {
            ws.send(JSON.stringify({
              type: 'pong',
              timestamp: new Date().toISOString(),
            }));
          }
        } catch (e) {
          // Non-JSON message — ignore
        }
      });

      ws.on('close', () => {
        const clients = global.__auditWsClients.get(auditId);
        if (clients) {
          clients.delete(ws);
          if (clients.size === 0) {
            global.__auditWsClients.delete(auditId);
          }
        }
      });

      ws.on('error', (error) => {
        console.error('[WS] Client error:', error.message);
      });

    } else {
      ws.close(4000, 'Invalid path — use /api/ws/audit/{auditId}');
    }
  });

  console.log('[WS] WebSocket bridge ready on /api/ws/audit/{auditId}');
}

function startAuditWorker() {
  try {
    // Worker runs as ESM — use dynamic require via tsx/ts-node if available
    // Falls back gracefully if TypeScript runtime not present
    require('./src/worker/audit-worker').startAuditWorker();
    console.log('[Worker] Audit worker started');
  } catch (err) {
    console.warn('[Worker] Could not start TypeScript worker directly:', err.message);
    console.warn('[Worker] Run: npx tsx src/worker/audit-worker.ts in production');
  }
}

app.prepare().then(() => {
  const server = createServer(async (req, res) => {
    try {
      const parsedUrl = parse(req.url, true);
      await handle(req, res, parsedUrl);
    } catch (err) {
      console.error('Error handling', req.url, err);
      res.statusCode = 500;
      res.end('internal server error');
    }
  });

  setupWebSocketServer(server);
  startAuditWorker();

  server.listen(port, () => {
    console.log(`> Ready on http://${hostname}:${port}`);
    console.log(`> WebSocket bridge: ws://${hostname}:${port}/api/ws/audit/{auditId}`);
    console.log(`> HexStrike API: ${process.env.HEXSTRIKE_API_URL || 'http://localhost:8000'}`);
  });
});
