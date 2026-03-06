/**
 * Types for AgentxploiTor
 */

export type JobStatus = 
  | 'pending_payment'
  | 'payment_verified'
  | 'queued'
  | 'in_progress'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

export interface StateHistoryEntry {
  status: JobStatus;
  timestamp: string;
  reason?: string;
}

export type AuditType = 'contract_basic' | 'contract_deep' | 'miniapp' | 'full_stack'
export type TargetType = 'contract_evm' | 'contract_solana' | 'github_repo' | 'miniapp_url'
export type PaymentToken = 'eth' | 'usdc' | 'bnkr'

export interface ResolvedTarget {
  type: TargetType
  value: string
  chain?: string
  sourceAvailable?: boolean
  confirmedByUser?: boolean
}

export interface JobSession {
  id: string;
  targetUrl: string;
  contractAddress?: string;
  // New fields — Group 2
  githubUrl?: string;
  blockchain?: string;
  auditType?: AuditType;
  targetType?: TargetType;
  rawInput?: string;
  resolvedTarget?: ResolvedTarget;
  discoveryTier?: 1 | 2 | 3;
  paymentToken?: PaymentToken;
  requestedByFid?: number;
  hexstrikeRequestId?: string;
  findings?: any[];
  overallSeverity?: string;
  confidenceScore?: number;
  agentsUsed?: string[];
  toolsUsed?: string[];
  // Original fields
  scope: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: JobStatus;
  createdBy?: string;
  walletAddress?: string;
  paymentTxHash?: string;
  paymentAmount?: string;
  paymentVerified?: boolean;
  findingsCount?: Record<string, number>;
  reportPath?: string;
  error?: string;
  createdAt: string;
  updatedAt: string;
  stateHistory: StateHistoryEntry[];
}

export type FindingStatus = 'open' | 'acknowledged' | 'fixed' | 'wont_fix' | 'false_positive';

export interface Vulnerability {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  cvssScore: number;
  location: string;
  exploitScenario: string;
  expectedOutcome: string;
  targetUrl?: string;
  analyzer?: string;
  confidence: number;
  status?: FindingStatus;
  aiSuggestion?: string;
  assignedTo?: string;
}

export interface Exploit {
  vulnerabilityId: string;
  technique: string;
  payload: string;
  steps: string[];
  successIndicators: string[];
  safetyConstraints: string[];
}

export interface VerificationResult {
  success: boolean;
  visualDiff: number;
  proofPath: string;
  evidence: string[];
  reason?: string;
  beforeUrl?: string;
  afterUrl?: string;
}

export interface SelfEvaluation {
  satisfactory: boolean;
  confidence: number;
  issues: string[];
  evidence: string[];
}

export interface AuditReport {
  id: string;
  jobId: string;
  targetUrl: string;
  summary: Record<string, number>;
  vulnerabilities: Vulnerability[];
  exploits: Exploit[];
  verifications: VerificationResult[];
  evaluation: SelfEvaluation;
  createdAt: string;
}

export interface PaymentVerificationResult {
  valid: boolean;
  amount?: bigint;
  blockNumber?: bigint;
  confirmations?: number;
  error?: string;
}
