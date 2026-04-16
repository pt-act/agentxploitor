# QuickNode Integration Tasks — AgentxploiTor

**Version:** 1.0 — 2026-03-21

## Overview
QuickNode integration for AgentxploiTor across 4 phases. Primary driver: replace Basescan API rate limits with direct RPC access. Secondary: state analysis, transaction tracing, multi-chain expansion, Solana support.

## Phases & Dependencies

```
Phase 1 (Base + Bytecode) ──► Phase 2 (State + Traces) ──► Phase 3 (Multi-Chain) ──► Phase 4 (Solana)
Groups 1-2                    Groups 3-4                   Group 5                   Group 6
~3 iterations                 ~4 iterations                ~1 iteration              ~2 iterations
```

---

## Phase 1: Base Chain + Bytecode

### Group 1: QuickNode Setup + Bytecode Fetching
- [x] 1.1 Enable QuickNode Build plan — create Base mainnet endpoint (`entityhex-base-main`) ✅ Endpoint ID: 604831, URL: `https://alpha-special-season.base-mainnet.quiknode.pro/...`
- [x] 1.2 Create `miniapp/src/lib/blockchain/quicknode-client.ts` — EVM RPC wrapper using `viem` (already in project)
- [x] 1.3 Implement `getBytecode(address: string, chain: string): Promise<Hex>` — call `eth_getCode` via QuickNode
- [x] 1.4 Update `miniapp/src/lib/chain-resolver.ts` — new resolution order:
  1. QuickNode `eth_getCode` for bytecode (always available, rate-unlimited)
  2. Basescan API for verified source code (ABI, source mapping — only if available)
  3. E2B Mythril bytecode analysis if no source
- [x] 1.5 Add `QUICKNODE_BASE_URL` and `QUICKNODE_API_KEY` to `.env.example`
- [x] 1.6 Add `QUICKNODE_ETH_URL`, `QUICKNODE_BSC_URL`, `QUICKNODE_POLY_URL` for future phases
- [x] 1.7 Enable MEV Protection & Gas Recovery by Merkle on Base endpoint ✅ (free add-on enabled)

### Group 2: State Analysis
- [x] 2.1 Implement `getStorageSlot(address, slot, chain): Promise<Hex>` — call `eth_getStorageAt` via QuickNode (in quicknode-client.ts)
- [x] 2.2 Implement proxy detection — read EIP-1967 implementation slot (in state-analyzer.ts)
- [x] 2.3 Detect admin/owner roles — read `Ownable.owner()` and `AccessControl` role slots (in state-analyzer.ts)
- [x] 2.4 Create `miniapp/src/lib/blockchain/state-analyzer.ts` (<400 lines)
- [x] 2.5 Feed state findings into ResolvedSource.onChainState — available to HexStrike VulnerabilityCorrelator
- [x] 2.6 Display state analysis in ContractAuditView — added `OnChainStatePanel` component showing bytecode size, proxy pattern, implementation address, admin/owner.

---

## Phase 2: Transaction Tracing + Monitoring

### Group 3: Transaction Tracing
- [x] 3.1 Implement `traceTransaction(txHash, chain): Promise<TraceResult>` — call `debug_traceTransaction` via QuickNode (in transaction-tracer.ts)
- [x] 3.2 Parse trace output into call tree for exploit path visualization — includes reentrancy detection + external-call-before-state detection
- [x] 3.3 Feed trace data into AIExploitGenerator for PoC validation (only for post-mortem of known exploits)
- [x] 3.4 Create `miniapp/src/lib/blockchain/transaction-tracer.ts` (<400 lines)
- [x] 3.5 Add trace visualization to results UI — interactive call tree with reentrancy warnings and external-call-before-state detection in `ContractAuditView.tsx`

### Group 4: Contract Monitoring (Phase 2 Foundation)
- [x] 4.1 Create `miniapp/src/lib/blockchain/chain-monitor.ts` — WebSocket block subscription + contract watching + change detection
- [x] 4.2 Monitor watched contracts for bytecode changes between blocks
- [x] 4.3 Detect admin role transfers, proxy upgrades, pause state changes
- [x] 4.4 Store monitoring state in persistent storage — in-memory with globalThis pattern (same as jobStore), ready for Vercel KV migration
- [x] 4.5 Create monitoring API endpoints — `POST /api/monitoring/watch`, `GET /api/monitoring/watch`, `DELETE /api/monitoring/watch`, `GET /api/monitoring/events`

---

## Phase 3: Multi-Chain Expansion

### Group 5: Ethereum + BSC + Polygon
- [x] 5.1 Enable QuickNode endpoints: Ethereum mainnet, BSC, Polygon ✅ Endpoints: 604866 (ETH), 604867 (BSC), 604868 (Polygon)
- [x] 5.2 Update `quicknode-client.ts` with multi-chain routing (chain → endpoint mapping) — already supports all 4 chains from creation
- [x] 5.3 Update chain auto-detection in TargetInputForm — route to correct endpoint (UI already shows chain in DetectionBadge: "⬡ EVM Contract · Base", "◎ Solana Program")
- [x] 5.4 Test contract analysis on Ethereum, BSC, Polygon contracts ✅ ETH: USDT contract (11,075 bytes) verified via QuickNode
- [x] 5.5 Update UI to show supported chains and "coming soon" for unsupported — DetectionBadge shows supported chains, unknown types show resolve error.

---

## Phase 4: Solana Integration

### Group 6: Solana Program Analysis
- [x] 6.1 Enable QuickNode Solana endpoint (`entityhex-solana-main`) ✅ Endpoint ID: 604830
- [x] 6.2 Create `miniapp/src/lib/blockchain/solana-client.ts` — `getAccountInfo()`, `getSolanaProgram()`, `getSlot()`, `getMultipleAccounts()`
- [x] 6.3 Extend chain-resolver `resolveSolanaProgram()` — now fetches on-chain program data via QuickNode (data size, upgrade authority)
- [x] 6.4 Extend HexStrike SolanaAnalyzerAdapter — feed live on-chain data alongside regex analysis — `solana-client.ts` provides `getSolanaProgram()` data that flows into chain-resolver
- [x] 6.5 Update TargetInputForm — accept Solana program addresses (base58 format detection) — DetectionBadge shows "◎ Solana Program" for Solana addresses
- [x] 6.6 Update UI — "Solana Program Audit" flow with chain-specific findings — `SolanaAuditResult.tsx` component shows on-chain program data + Solana-specific findings

---

## Parallelization Strategy

| Phase | Dev A (Backend/Blockchain) | Dev B (Frontend) |
|---|---|---|
| Phase 1 | Groups 1.1–1.4, 2.1–2.5 | Groups 1.5–1.6, 2.6 (UI display) |
| Phase 2 | Groups 3.1–3.4, 4.1–4.4 | Groups 3.5, 4.5 (UI + API) |
| Phase 3 | Group 5.1–5.2 | Groups 5.3–5.5 (UI + testing) |
| Phase 4 | Groups 6.1–6.4 | Groups 6.5–6.6 (UI) |

## Iteration Estimates

| Group | Iterations | Notes |
|---|---|---|
| Group 1: Setup + Bytecode | 2 | Replace Basescan API dependency |
| Group 2: State Analysis | 2 | New capability |
| Group 3: Transaction Tracing | 2 | New capability |
| Group 4: Contract Monitoring | 2 | Phase 2 foundation |
| Group 5: Multi-Chain | 1 | Endpoint routing |
| Group 6: Solana | 2 | Program analysis extension |
| **Total** | **~11** | **~7 parallelized across 2 devs** |

## Relationship to EntityHex Spec

This QuickNode spec sits alongside the entityhex spec (Groups 0-6). The entityhex spec covers the miniapp UI, HexStrike integration, and audit pipeline. This QuickNode spec covers the **on-chain data layer** that feeds into that pipeline.

```
entityhex spec (Groups 0-6):
  Target Input → EntityHex Security Agent → HexStrike → E2B → Report

quicknode spec (Groups 1-6):
  Contract Address → QuickNode RPC → Bytecode/State/Trace → feeds into entityhex pipeline
```

They run in parallel. QuickNode Groups 1-2 can be implemented while entityhex Groups 5-6 are in progress.

---

*Last updated: 2026-03-21*
