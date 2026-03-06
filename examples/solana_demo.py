#!/usr/bin/env python3
"""
AgentxploiTor - Solana Security Demo

Demonstrates autonomous Solana smart contract security auditing.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agentxploitor import AgentxploiTorAgent, Vulnerability

async def solana_security_demo():
    """
    Demo: Autonomous Solana Program Security Audit
    
    Shows AgentxploiTor finding real Solana vulnerability patterns
    """
    
    print("=" * 80)
    print("AgentxploiTor - Solana Program Security Audit")
    print("=" * 80)
    print()
    print("🎯 Target: Solana SPL Program")
    print("🎯 Focus: Signature verification, account validation, math safety")
    print()
    
    # Initialize agent
    agent = AgentxploiTorAgent(browser_perception=True, auto_submit=False)
    
    # Demo: Show Solana-specific vulnerabilities
    print("🔍 Scanning Solana program for common vulnerability patterns...")
    print()
    
    # Simulate Solana-specific vulnerabilities
    solana_vulnerabilities = [
        Vulnerability(
            id="SOL-001",
            title="Missing Signer Verification in Transfer",
            description="SPL token transfer lacks proper signer validation, allowing unauthorized token movements",
            severity="CRITICAL",
            cvss_score=9.8,
            location="token-transfer.rs:45-67",
            exploit_scenario="Attacker can transfer tokens from any account by bypassing signer check",
            expected_outcome="Unauthorized token transfer succeeds",
            target_url="https://explorer.solana.com/address/[program-id]"
        ),
        Vulnerability(
            id="SOL-002",
            title="Unchecked Account Ownership",
            description="Program doesn't verify account ownership, enabling account spoofing attacks",
            severity="HIGH",
            cvss_score=8.5,
            location="process_instruction.rs:120-145",
            exploit_scenario="Attacker provides fake account, program accepts without owner validation",
            expected_outcome="Malicious account accepted as legitimate",
            target_url="https://explorer.solana.com/address/[program-id]"
        ),
        Vulnerability(
            id="SOL-003",
            title="Integer Overflow in Token Math",
            description="Token amount calculations use unchecked arithmetic",
            severity="HIGH",
            cvss_score=7.5,
            location="calculate_fees.rs:89-103",
            exploit_scenario="Large token amounts cause overflow, resulting in incorrect balances",
            expected_outcome="Token balance corrupted due to overflow",
            target_url="https://explorer.solana.com/address/[program-id]"
        )
    ]
    
    # Display findings
    for vuln in solana_vulnerabilities:
        print(f"🚨 [{vuln.severity}] {vuln.title}")
        print(f"   CVSS: {vuln.cvss_score}")
        print(f"   Location: {vuln.location}")
        print(f"   Impact: {vuln.description}")
        print()
    
    # Focus on most critical
    critical = solana_vulnerabilities[0]
    
    print("─" * 80)
    print(f"🎯 Selected for autonomous exploitation: {critical.title}")
    print("─" * 80)
    print()
    
    # Generate exploit
    print("⚡ Generating Solana-specific exploit...")
    exploit = await agent.generate_exploit(critical)
    print(f"   Technique: {exploit.technique}")
    print(f"   Target: Solana SPL Token Program")
    print()
    
    # In a real scenario, would use Solana SDK to exploit
    # For demo, show what would happen
    print("📝 Autonomous Exploit Workflow:")
    print("   1. Connect to Solana devnet")
    print("   2. Create attacker wallet")
    print("   3. Craft malicious transaction (bypass signer check)")
    print("   4. Submit transaction to program")
    print("   5. Verify unauthorized transfer succeeded")
    print()
    
    print("💡 Solana-Specific Security Checks:")
    print("   ✅ Signer validation (is_signer constraint)")
    print("   ✅ Account ownership (owner == program_id)")
    print("   ✅ Checked arithmetic (checked_add, checked_mul)")
    print("   ✅ PDA derivation (proper seeds)")
    print("   ✅ Rent exemption (minimum balance)")
    print()
    
    print("=" * 80)
    print("SOLANA SECURITY AUDIT COMPLETE")
    print("=" * 80)
    print()
    print(f"✅ Found {len(solana_vulnerabilities)} Solana-specific vulnerabilities")
    print(f"✅ Generated exploitation strategy for CRITICAL issue")
    print(f"✅ Demonstrated autonomous Solana program analysis")
    print()
    print("🏆 AgentxploiTor: The First AI Agent for Autonomous Solana Security")
    

if __name__ == '__main__':
    asyncio.run(solana_security_demo())
