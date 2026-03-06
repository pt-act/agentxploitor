/**
 * Job Storage for AgentxploiTor
 * In-memory storage with optional Vercel KV integration
 */

import type { JobSession, AuditReport } from './types';

export interface JobStore {
  get(id: string): Promise<JobSession | null>;
  set(id: string, job: JobSession): Promise<void>;
  update(id: string, updates: Partial<JobSession>): Promise<void>;
  delete(id: string): Promise<void>;
  list(walletAddress?: string): Promise<JobSession[]>;
  enqueue(id: string): Promise<void>;
  dequeue(): Promise<JobSession | null>;
}

export interface ReportStore {
  get(id: string): Promise<AuditReport | null>;
  set(id: string, report: AuditReport): Promise<void>;
  delete(id: string): Promise<void>;
}

declare global {
  // eslint-disable-next-line no-var
  var __jobStore: Map<string, JobSession> | undefined;
  // eslint-disable-next-line no-var
  var __jobQueue: string[] | undefined;
  // eslint-disable-next-line no-var
  var __reportStore: Map<string, AuditReport> | undefined;
}

class MemoryJobStore implements JobStore {
  private store: Map<string, JobSession>;
  private queue: string[];

  constructor() {
    if (typeof globalThis !== 'undefined') {
      if (!globalThis.__jobStore) {
        globalThis.__jobStore = new Map();
      }
      if (!globalThis.__jobQueue) {
        globalThis.__jobQueue = [];
      }
      this.store = globalThis.__jobStore;
      this.queue = globalThis.__jobQueue;
    } else {
      this.store = new Map();
      this.queue = [];
    }
  }

  async get(id: string): Promise<JobSession | null> {
    return this.store.get(id) || null;
  }

  async set(id: string, job: JobSession): Promise<void> {
    this.store.set(id, job);
  }

  async update(id: string, updates: Partial<JobSession>): Promise<void> {
    const existing = this.store.get(id);
    if (existing) {
      this.store.set(id, { ...existing, ...updates, updatedAt: new Date().toISOString() });
    }
  }

  async delete(id: string): Promise<void> {
    this.store.delete(id);
    const idx = this.queue.indexOf(id);
    if (idx >= 0) this.queue.splice(idx, 1);
  }

  async list(walletAddress?: string): Promise<JobSession[]> {
    const jobs = Array.from(this.store.values());
    if (walletAddress) {
      return jobs.filter(j => j.walletAddress?.toLowerCase() === walletAddress.toLowerCase());
    }
    return jobs.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }

  async enqueue(id: string): Promise<void> {
    if (!this.queue.includes(id)) {
      this.queue.push(id);
    }
  }

  async dequeue(): Promise<JobSession | null> {
    const id = this.queue.shift();
    if (id) {
      return this.store.get(id) || null;
    }
    return null;
  }
}

class MemoryReportStore implements ReportStore {
  private store: Map<string, AuditReport>;

  constructor() {
    if (typeof globalThis !== 'undefined') {
      if (!globalThis.__reportStore) {
        globalThis.__reportStore = new Map();
      }
      this.store = globalThis.__reportStore;
    } else {
      this.store = new Map();
    }
  }

  async get(id: string): Promise<AuditReport | null> {
    return this.store.get(id) || null;
  }

  async set(id: string, report: AuditReport): Promise<void> {
    this.store.set(id, report);
  }

  async delete(id: string): Promise<void> {
    this.store.delete(id);
  }
}

export const jobStore = new MemoryJobStore();
export const reportStore = new MemoryReportStore();

export async function getJob(id: string): Promise<JobSession | null> {
  return jobStore.get(id);
}

export interface CreateJobInput {
  id: string;
  targetUrl: string;
  contractAddress?: string;
  // New fields — Group 2
  githubUrl?: string;
  blockchain?: string;
  auditType?: import('./types').AuditType;
  targetType?: import('./types').TargetType;
  rawInput?: string;
  resolvedTarget?: import('./types').ResolvedTarget;
  discoveryTier?: 1 | 2 | 3;
  paymentToken?: import('./types').PaymentToken;
  requestedByFid?: number;
  // FarCaster Miniapp Auditor fields
  persona?: import('./types').Persona;
  mode?: import('./types').AuditMode;
  analysisType?: import('./types').AnalysisType;
  // Original fields
  scope: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: JobSession['status'];
  createdBy?: string;
  walletAddress?: string;
  paymentTxHash?: string;
  paymentAmount?: string;
  paymentVerified?: boolean;
}

export async function createJob(data: CreateJobInput): Promise<JobSession> {
  const now = new Date().toISOString();
  const job: JobSession = {
    ...data,
    createdAt: now,
    updatedAt: now,
    stateHistory: [{
      status: data.status,
      timestamp: now,
    }],
  };
  await jobStore.set(job.id, job);
  return job;
}

export async function updateJobStatus(
  id: string,
  status: JobSession['status'],
  reason?: string
): Promise<JobSession | null> {
  const job = await jobStore.get(id);
  if (!job) return null;
  
  const now = new Date().toISOString();
  const validTransitions: Record<string, string[]> = {
    pending_payment: ['payment_verified', 'queued', 'cancelled'],
    payment_verified: ['queued', 'in_progress', 'cancelled'],
    queued: ['in_progress', 'cancelled'],
    in_progress: ['completed', 'failed', 'cancelled'],
    completed: [],
    failed: ['queued'],
    cancelled: ['queued'],
  };
  
  if (!validTransitions[job.status]?.includes(status)) {
    throw new Error(`Invalid transition from ${job.status} to ${status}`);
  }
  
  const updated: JobSession = {
    ...job,
    status,
    updatedAt: now,
    stateHistory: [
      ...job.stateHistory,
      { status, timestamp: now, reason },
    ],
  };
  
  await jobStore.set(id, updated);
  return updated;
}
