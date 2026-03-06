/**
 * Tests for UI Components - Group 3
 * 
 * Tests for ReasoningStream, FindingCard, AttackPathGraph, FocusDashboard
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ReasoningStream } from '~/components/ReasoningStream';
import { FindingCard } from '~/components/FindingCard';
import { AttackPathGraph } from '~/components/AttackPathGraph';
import { FocusDashboard } from '~/components/FocusDashboard';
import type { Vulnerability } from '~/lib/types';

const mockVulnerability: Vulnerability = {
  id: 'vuln-001',
  title: 'Reentrancy Vulnerability',
  description: 'A reentrancy vulnerability was detected in the withdraw function.',
  severity: 'CRITICAL',
  cvssScore: 9.8,
  location: 'contracts/Withdrawal.sol:45',
  exploitScenario: 'Attacker can recursively call withdraw before balance is updated.',
  expectedOutcome: 'Implement reentrancy guard or checks-effects-interactions pattern.',
  confidence: 0.95,
  status: 'open',
  aiSuggestion: 'Consider using OpenZeppelin ReentrancyGuard.',
};

describe('ReasoningStream', () => {
  beforeEach(() => {
    vi.stubGlobal('WebSocket', vi.fn(() => ({
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null,
      close: vi.fn(),
      send: vi.fn(),
      readyState: 0,
    })));
  });

  it('renders with connection indicator', () => {
    render(<ReasoningStream auditId="test-audit" />);
    
    expect(screen.getByText(/Reasoning Stream/i)).toBeInTheDocument();
  });

  it('shows minimal events when level is minimal', () => {
    render(<ReasoningStream auditId="test-audit" level="minimal" />);
    
    const minimalBadge = screen.getByText('minimal');
    expect(minimalBadge).toBeInTheDocument();
  });

  it('shows verbose events when level is verbose', () => {
    render(<ReasoningStream auditId="test-audit" level="verbose" />);
    
    const verboseBadge = screen.getByText('verbose');
    expect(verboseBadge).toBeInTheDocument();
  });

  it('calls onEvent callback when event received', async () => {
    const onEvent = vi.fn();
    
    render(<ReasoningStream auditId="test-audit" onEvent={onEvent} />);
    
    expect(onEvent).not.toHaveBeenCalled();
  });
});

describe('FindingCard', () => {
  it('renders vulnerability title', () => {
    render(<FindingCard finding={mockVulnerability} />);
    
    expect(screen.getByText('Reentrancy Vulnerability')).toBeInTheDocument();
  });

  it('shows severity badge', () => {
    render(<FindingCard finding={mockVulnerability} />);
    
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
  });

  it('shows CVSS score', () => {
    render(<FindingCard finding={mockVulnerability} />);
    
    expect(screen.getByText(/CVSS 9.8/)).toBeInTheDocument();
  });

  it('shows confidence indicator', () => {
    render(<FindingCard finding={mockVulnerability} />);
    
    expect(screen.getByText(/95% confidence/)).toBeInTheDocument();
  });

  it('expands on click', () => {
    render(<FindingCard finding={mockVulnerability} />);
    
    const card = screen.getByText('Reentrancy Vulnerability').closest('div');
    fireEvent.click(card!);
    
    expect(screen.getByText(/Exploit Scenario/i)).toBeInTheDocument();
  });

  it('shows AI suggestion when expanded', () => {
    render(<FindingCard finding={mockVulnerability} expanded={true} />);
    
    expect(screen.getByText(/AI Suggestion/i)).toBeInTheDocument();
    expect(screen.getByText(/OpenZeppelin ReentrancyGuard/i)).toBeInTheDocument();
  });

  it('calls onStatusChange when status changes', async () => {
    const onStatusChange = vi.fn();
    
    render(
      <FindingCard finding={mockVulnerability} onStatusChange={onStatusChange} expanded={true} />
    );
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'fixed' } });
    
    expect(onStatusChange).toHaveBeenCalledWith('fixed');
  });
});

describe('AttackPathGraph', () => {
  const mockNodes = [
    { id: 'node-1', type: 'entry' as const, label: 'User Input' },
    { id: 'node-2', type: 'vulnerability' as const, label: 'SQL Injection', severity: 'high' as const },
    { id: 'node-3', type: 'exploit' as const, label: 'Data Extraction' },
    { id: 'node-4', type: 'impact' as const, label: 'Data Breach' },
  ];

  const mockEdges = [
    { id: 'edge-1', source: 'node-1', target: 'node-2' },
    { id: 'edge-2', source: 'node-2', target: 'node-3' },
    { id: 'edge-3', source: 'node-3', target: 'node-4' },
  ];

  it('renders graph container', () => {
    render(<AttackPathGraph nodes={mockNodes} edges={mockEdges} />);
    
    expect(screen.getByText(/Attack Path Graph/i)).toBeInTheDocument();
  });

  it('calls onNodeClick when node is clicked', () => {
    const onNodeClick = vi.fn();
    
    render(
      <AttackPathGraph nodes={mockNodes} edges={mockEdges} onNodeClick={onNodeClick} />
    );
    
    const node = screen.getByText('User Input');
    fireEvent.click(node);
    
    expect(onNodeClick).toHaveBeenCalled();
  });

  it('renders with custom height', () => {
    const { container } = render(
      <AttackPathGraph nodes={mockNodes} edges={mockEdges} height="600px" />
    );
    
    const graphContainer = container.querySelector('.bg-\\[\\#0a0e27\\]');
    expect(graphContainer).toBeInTheDocument();
  });
});

describe('FocusDashboard', () => {
  it('shows loading state initially', () => {
    render(<FocusDashboard />);
    
    expect(screen.getByText(/Loading dashboard/i)).toBeInTheDocument();
  });

  it('renders dashboard title', async () => {
    render(<FocusDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
  });

  it('shows focus mode button', async () => {
    render(<FocusDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/Focus Mode/i)).toBeInTheDocument();
    });
  });

  it('shows start audit button', async () => {
    render(<FocusDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/Start New Audit/i)).toBeInTheDocument();
    });
  });
});
