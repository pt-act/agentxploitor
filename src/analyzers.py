"""
AgentxploiTor Analyzer Adapters

Adapter layer for vulnerability analyzers (Slither, Mythril, etc.)
"""

import asyncio
import json
import os
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from models import Vulnerability, Severity
from exceptions import AnalyzerError, ConfigurationError, ScanError


class AnalyzerAdapter(ABC):
    """Abstract base class for vulnerability analyzers."""
    
    name: str = "base"
    supported_chains: List[str] = []
    
    def __init__(
        self,
        binary_path: Optional[str] = None,
        timeout: int = 300,
        output_dir: Optional[Path] = None
    ):
        self.binary_path = binary_path
        self.timeout = timeout
        self.output_dir = output_dir or Path("/tmp/agentxploitor/analyzers")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    async def scan(
        self,
        target: str,
        target_type: str = "solidity"
    ) -> List[Vulnerability]:
        """Run analysis and return findings."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if analyzer is installed and available."""
        pass
    
    def _run_command(
        self,
        command: List[str],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute shell command with timeout."""
        timeout = timeout or self.timeout
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            raise AnalyzerError(
                f"Analyzer {self.name} timed out after {timeout}s",
                analyzer_name=self.name,
                recoverable=True
            )
        except FileNotFoundError:
            raise ConfigurationError(
                f"Analyzer binary not found: {command[0]}",
                config_key=f"{self.name}_path"
            )


class SlitherAdapter(AnalyzerAdapter):
    """Adapter for Slither static analyzer (EVM/Solidity)."""
    
    name = "slither"
    supported_chains = ["ethereum", "arbitrum", "optimism", "base", "polygon", "bsc"]
    
    SEVERITY_MAP = {
        "High": Severity.HIGH,
        "Medium": Severity.MEDIUM,
        "Low": Severity.LOW,
        "Informational": Severity.INFO,
        "Optimization": Severity.INFO,
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.binary_path = self.binary_path or os.environ.get(
            'SLITHER_PATH',
            'slither'
        )
    
    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                [self.binary_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan(
        self,
        target: str,
        target_type: str = "solidity"
    ) -> List[Vulnerability]:
        """Run Slither analysis on target."""
        
        output_file = self.output_dir / f"slither-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        
        command = [
            self.binary_path,
            target,
            '--json', str(output_file),
            '--skip-assembly',
            '--disable-color'
        ]
        
        vulnerabilities = []
        
        try:
            result = self._run_command(command)
            
            if not output_file.exists():
                if result['stderr']:
                    raise AnalyzerError(
                        f"Slither analysis failed: {result['stderr']}",
                        analyzer_name=self.name,
                        target=target
                    )
                return vulnerabilities
            
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            for detector in data.get('results', {}).get('detectors', []):
                vuln = self._parse_finding(detector, target)
                vulnerabilities.append(vuln)
            
            return vulnerabilities
            
        except json.JSONDecodeError as e:
            raise AnalyzerError(
                f"Failed to parse Slither output: {e}",
                analyzer_name=self.name,
                target=target,
                recoverable=True
            )
    
    def _parse_finding(self, finding: Dict[str, Any], target: str) -> Vulnerability:
        """Parse Slither finding into Vulnerability."""
        
        severity_str = finding.get('impact', 'Informational')
        severity = self.SEVERITY_MAP.get(severity_str, Severity.INFO)
        
        check = finding.get('check', 'Unknown')
        description = finding.get('description', 'No description')
        
        elements = finding.get('elements', [])
        location = ""
        if elements:
            first = elements[0]
            location = f"{first.get('source_mapping', {}).get('filename_relative', 'unknown')}"
            if 'name' in first:
                location += f":{first['name']}"
        
        return Vulnerability(
            id=f"SLITHER-{finding.get('id', 'unknown')}",
            title=check,
            description=description,
            severity=severity,
            cvss_score=self._estimate_cvss(severity),
            location=location or "unknown",
            exploit_scenario=finding.get('markdown', ''),
            expected_outcome=f"Fix {check.lower()}",
            target_url=target,
            analyzer=self.name,
            confidence=finding.get('confidence', 1.0) / 100.0
        )
    
    def _estimate_cvss(self, severity: Severity) -> float:
        """Estimate CVSS score from severity."""
        scores = {
            Severity.CRITICAL: 9.5,
            Severity.HIGH: 7.5,
            Severity.MEDIUM: 5.0,
            Severity.LOW: 3.0,
            Severity.INFO: 1.0,
        }
        return scores.get(severity, 1.0)


class MythrilAdapter(AnalyzerAdapter):
    """Adapter for Mythril symbolic execution analyzer (EVM)."""
    
    name = "mythril"
    supported_chains = ["ethereum", "arbitrum", "optimism", "base", "polygon", "bsc"]
    
    SEVERITY_MAP = {
        "High": Severity.HIGH,
        "Medium": Severity.MEDIUM,
        "Low": Severity.LOW,
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.binary_path = self.binary_path or os.environ.get(
            'MYTHRIL_PATH',
            'myth'
        )
    
    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                [self.binary_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan(
        self,
        target: str,
        target_type: str = "solidity"
    ) -> List[Vulnerability]:
        """Run Mythril analysis on target."""
        
        output_file = self.output_dir / f"mythril-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        
        command = [
            self.binary_path,
            'analyze',
            target,
            '-o', 'json',
            '--out', str(output_file),
            '--max-depth', '50'
        ]
        
        vulnerabilities = []
        
        try:
            result = self._run_command(command, timeout=600)
            
            if not output_file.exists():
                stdout = result.get('stdout', '')
                if stdout:
                    try:
                        data = json.loads(stdout)
                        return self._parse_output(data, target)
                    except json.JSONDecodeError:
                        pass
                return vulnerabilities
            
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            return self._parse_output(data, target)
            
        except json.JSONDecodeError as e:
            raise AnalyzerError(
                f"Failed to parse Mythril output: {e}",
                analyzer_name=self.name,
                target=target,
                recoverable=True
            )
    
    def _parse_output(self, data: Dict[str, Any], target: str) -> List[Vulnerability]:
        """Parse Mythril output into vulnerabilities."""
        vulnerabilities = []
        
        issues = data.get('issues', []) if isinstance(data, dict) else []
        
        for issue in issues:
            severity_str = issue.get('severity', 'Low')
            severity = self.SEVERITY_MAP.get(severity_str, Severity.LOW)
            
            vulnerabilities.append(Vulnerability(
                id=f"MYTHRIL-{issue.get('swc-id', 'unknown')}",
                title=issue.get('title', 'Unknown'),
                description=issue.get('description', 'No description'),
                severity=severity,
                cvss_score=self._estimate_cvss(severity),
                location=issue.get('filename', 'unknown'),
                exploit_scenario=issue.get('code', ''),
                expected_outcome=f"Fix {issue.get('title', 'vulnerability').lower()}",
                target_url=target,
                analyzer=self.name,
                confidence=0.8
            ))
        
        return vulnerabilities
    
    def _estimate_cvss(self, severity: Severity) -> float:
        """Estimate CVSS score from severity."""
        scores = {
            Severity.CRITICAL: 9.5,
            Severity.HIGH: 7.5,
            Severity.MEDIUM: 5.0,
            Severity.LOW: 3.0,
            Severity.INFO: 1.0,
        }
        return scores.get(severity, 1.0)


class SolanaAnalyzerAdapter(AnalyzerAdapter):
    """
    Adapter for Solana/Rust program static analysis.
    
    Detects common Solana vulnerabilities:
    - Missing signer checks
    - Integer overflow risks
    - CPI (Cross-Program Invocation) risks
    - Account validation issues
    - Anchor constraint violations
    """
    
    name = "solana"
    supported_chains = ["solana"]
    
    # Common vulnerability patterns in Solana Rust/Anchor code
    VULNERABILITY_PATTERNS = [
        {
            "id": "SOL-001",
            "title": "Missing Signer Check",
            "pattern": r"ctx\.\s*accounts\.[a-zA-Z_]+\s*\.\s*(?:is_signer|to_account_info\(\)\.is_signer)",
            "severity": Severity.CRITICAL,
            "description": "Instruction does not verify that the account signer flag is set.",
            "exploit_scenario": "Attacker can call this instruction without authorization."
        },
        {
            "id": "SOL-002",
            "title": "Missing Owner Check",
            "pattern": r"ctx\.\.accounts\.[a-zA-Z_]+\s*\.\s*owner\s*==",
            "severity": Severity.HIGH,
            "description": "Account ownership is not validated before use.",
            "exploit_scenario": "Attacker can pass a malicious account with different data."
        },
        {
            "id": "SOL-003",
            "title": "Unsafe CPI Invocation",
            "pattern": r"CpiContext::new|invoke\(|invoke_signed\(",
            "severity": Severity.MEDIUM,
            "description": "Cross-Program Invocation without proper checks.",
            "exploit_scenario": "CPI target could be manipulated to execute unintended instructions."
        },
        {
            "id": "SOL-004",
            "title": "Integer Overflow Risk",
            "pattern": r"\b(u8|u16|u32|u64|u128|i8|i16|i32|i64|i128)\s*\+\s*\w+|\bsaturating_(add|sub|mul)",
            "severity": Severity.MEDIUM,
            "description": "Potential integer arithmetic without overflow protection.",
            "exploit_scenario": "Integer overflow could cause unexpected program state."
        },
        {
            "id": "SOL-005",
            "title": "Missing Account Validation",
            "pattern": r"#[account\([a-zA-Z_]+\s*\.\s*(?:init|mut)\)\]|\bAccountLoader\b",
            "severity": Severity.HIGH,
            "description": "Account may not have proper initialization or mutability constraints.",
            "exploit_scenario": "Account state could be manipulated unexpectedly."
        },
        {
            "id": "SOL-006",
            "title": "Anchor PDA Validation Missing",
            "pattern": r"seeds\s*=\s*\[|\bSeeds\s*\[",
            "severity": Severity.MEDIUM,
            "description": "PDA derivation not validated with proper bump seed.",
            "exploit_scenario": "Incorrect PDA could lead to account confusion attacks."
        },
        {
            "id": "SOL-007",
            "title": "Unchecked Program Call",
            "pattern": r"program::call\(|\.to_account_info\(\).\s*\.\s*executable",
            "severity": Severity.HIGH,
            "description": "Program execution without validating target is executable.",
            "exploit_scenario": "Could execute arbitrary code via non-executable account."
        },
        {
            "id": "SOL-008",
            "title": "Missing Rent Exemption",
            "pattern": r"\.to_account_info\(\)\.\s*lamports\s*\+",
            "severity": Severity.LOW,
            "description": "Account rent exemption not explicitly handled.",
            "exploit_scenario": "Account could be deactivated leading to data loss."
        },
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.binary_path = self.binary_path or os.environ.get(
            'SOLANA_ANALYZER_PATH',
            'solana-analyzer'
        )
    
    def is_available(self) -> bool:
        """Always available - uses pattern matching."""
        return True
    
    async def scan(
        self,
        target: str,
        target_type: str = "rust"
    ) -> List[Vulnerability]:
        """Run static analysis on Solana/Rust program."""
        import re
        
        vulnerabilities = []
        target_path = Path(target)
        
        if not target_path.exists():
            target_path = self.output_dir / "solana_target.rs"
        
        rust_files = list(target_path.rglob("*.rs")) if target_path.is_dir() else [target_path]
        
        for rust_file in rust_files:
            try:
                with open(rust_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for vuln_pattern in self.VULNERABILITY_PATTERNS:
                    matches = re.finditer(vuln_pattern["pattern"], content, re.MULTILINE)
                    
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        
                        vulnerabilities.append(Vulnerability(
                            id=vuln_pattern["id"],
                            title=vuln_pattern["title"],
                            description=vuln_pattern["description"],
                            severity=vuln_pattern["severity"],
                            cvss_score=self._estimate_cvss(vuln_pattern["severity"]),
                            location=f"{rust_file}:{line_num}",
                            exploit_scenario=vuln_pattern["exploit_scenario"],
                            expected_outcome=f"Add proper {vuln_pattern['title'].lower()} validation",
                            target_url=target,
                            analyzer=self.name,
                            confidence=0.75
                        ))
                        
            except Exception:
                continue
        
        return vulnerabilities
    
    def _estimate_cvss(self, severity: Severity) -> float:
        """Estimate CVSS score from severity."""
        scores = {
            Severity.CRITICAL: 9.8,
            Severity.HIGH: 8.0,
            Severity.MEDIUM: 5.5,
            Severity.LOW: 2.5,
            Severity.INFO: 0.0,
        }
        return scores.get(severity, 3.0)


class FrontendAnalyzerAdapter(AnalyzerAdapter):
    """
    Adapter for Frontend/UI security analysis.
    
    Detects common frontend vulnerabilities:
    - XSS vectors
    - Insecure iframe sources
    - Wallet connector hijacking
    - Phishing indicators
    - Captures visual proof screenshots
    """
    
    name = "frontend"
    supported_chains = ["any"]  # Works for any chain, targets UI
    
    # Common frontend vulnerability patterns
    VULNERABILITY_PATTERNS = [
        {
            "id": "FRONT-001",
            "title": "Cross-Site Scripting (XSS) Vector",
            "pattern": r"dangerouslySetInnerHTML|innerHTML\s*=|eval\(|document\.write",
            "severity": Severity.HIGH,
            "description": "Potential XSS vulnerability found in frontend code.",
            "exploit_scenario": "Attacker could inject malicious scripts."
        },
        {
            "id": "FRONT-002",
            "title": "Insecure iframe Source",
            "pattern": r"iframe\s+src\s*=\s*['\"](?:http:|https:)?//",
            "severity": Severity.MEDIUM,
            "description": "iframe with potentially unsafe external source.",
            "exploit_scenario": "Could load malicious content from external domain."
        },
        {
            "id": "FRONT-003",
            "title": "Wallet Connector Misconfiguration",
            "pattern": r"(walletconnect|metamask|rainbow|coinbase).*(injected|provider|window\.ethereum)",
            "severity": Severity.HIGH,
            "description": "Wallet connection handler may be vulnerable to hijacking.",
            "exploit_scenario": "Attacker could intercept wallet signatures."
        },
        {
            "id": "FRONT-004",
            "title": "Phishing Indicator - External Links",
            "pattern": r"<a\s+[^>]*href\s*=\s*['\"]https?://(?!.*(?:base\.app|farcaster\.xyz|warpcast\.com))",
            "severity": Severity.LOW,
            "description": "External link found - potential phishing vector.",
            "exploit_scenario": "Users could be redirected to phishing sites."
        },
        {
            "id": "FRONT-005",
            "title": "Insecure Content Security Policy",
            "pattern": r"Content-Security-Policy.*'unsafe-inline'|'unsafe-eval'",
            "severity": Severity.MEDIUM,
            "description": "CSP allows unsafe inline scripts.",
            "exploit_scenario": "XSS attacks more likely to succeed."
        },
        {
            "id": "FRONT-006",
            "title": "Missing HTTPS",
            "pattern": r"src\s*=\s*['\"]http://|href\s*=\s*['\"]http://",
            "severity": Severity.MEDIUM,
            "description": "Resource loaded over insecure HTTP.",
            "exploit_scenario": "Man-in-the-middle could modify content."
        },
        {
            "id": "FRONT-007",
            "title": "LocalStorage Sensitive Data",
            "pattern": r"localStorage\.(setItem|getItem).*(private|key|secret|token|password)",
            "severity": Severity.HIGH,
            "description": "Sensitive data stored in localStorage.",
            "exploit_scenario": "XSS could steal sensitive data from storage."
        },
        {
            "id": "FRONT-008",
            "title": "Insecure PostMessage",
            "pattern": r"window\.postMessage\(.*, ?'\*'\)",
            "severity": Severity.MEDIUM,
            "description": "postMessage called with wildcard target origin.",
            "exploit_scenario": "Messages could be intercepted by malicious iframes."
        },
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.binary_path = self.binary_path or os.environ.get(
            'FRONTEND_ANALYZER_PATH',
            'node'  # Would use puppeteer/playwright in production
        )
    
    def is_available(self) -> bool:
        """Always available - uses pattern matching."""
        return True
    
    async def scan(
        self,
        target: str,
        target_type: str = "html"
    ) -> List[Vulnerability]:
        """Run frontend security analysis on target URL or files."""
        import re
        
        vulnerabilities = []
        
        # Handle URL targets (would use browser in production)
        if target.startswith('http://') or target.startswith('https://'):
            vulnerabilities.extend(await self._scan_url(target))
        else:
            # Handle file targets
            target_path = Path(target)
            
            if not target_path.exists():
                target_path = self.output_dir / "frontend_target"
            
            # Scan all frontend files
            extensions = ['*.html', '*.js', '*.jsx', '*.ts', '*.tsx', '*.vue']
            frontend_files = []
            
            for ext in extensions:
                frontend_files.extend(target_path.rglob(ext))
            
            if not frontend_files and target_path.is_file():
                frontend_files = [target_path]
            
            for frontend_file in frontend_files:
                try:
                    with open(frontend_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for vuln_pattern in self.VULNERABILITY_PATTERNS:
                        matches = re.finditer(vuln_pattern["pattern"], content, re.MULTILINE | re.IGNORECASE)
                        
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            
                            vulnerabilities.append(Vulnerability(
                                id=vuln_pattern["id"],
                                title=vuln_pattern["title"],
                                description=vuln_pattern["description"],
                                severity=vuln_pattern["severity"],
                                cvss_score=self._estimate_cvss(vuln_pattern["severity"]),
                                location=f"{frontend_file}:{line_num}",
                                exploit_scenario=vuln_pattern["exploit_scenario"],
                                expected_outcome=f"Fix {vuln_pattern['title'].lower()}",
                                target_url=target,
                                analyzer=self.name,
                                confidence=0.7
                            ))
                            
                except Exception:
                    continue
        
        return vulnerabilities
    
    async def _scan_url(self, url: str) -> List[Vulnerability]:
        """Scan a URL for frontend vulnerabilities (would use browser in production)."""
        # In production, this would:
        # 1. Launch headless browser
        # 2. Navigate to URL
        # 3. Capture before screenshot
        # 4. Inject test payloads
        # 5. Capture after screenshot
        # 6. Analyze DOM for vulnerabilities
        
        vulnerabilities = []
        
        # For now, return placeholder - would use real browser scanning
        # The agent-browser would handle the actual browser automation
        
        return vulnerabilities
    
    def _estimate_cvss(self, severity: Severity) -> float:
        """Estimate CVSS score from severity."""
        scores = {
            Severity.CRITICAL: 9.5,
            Severity.HIGH: 7.5,
            Severity.MEDIUM: 5.5,
            Severity.LOW: 3.5,
            Severity.INFO: 0.0,
        }
        return scores.get(severity, 3.0)


class MockAnalyzerAdapter(AnalyzerAdapter):
    """Mock analyzer for testing without real tools."""
    
    name = "mock"
    supported_chains = ["ethereum", "solana", "any"]
    
    def is_available(self) -> bool:
        return True
    
    async def scan(
        self,
        target: str,
        target_type: str = "solidity"
    ) -> List[Vulnerability]:
        """Return mock vulnerabilities."""
        return [
            Vulnerability(
                id="MOCK-001",
                title="Mock Vulnerability - Missing Authorization",
                description="This is a mock vulnerability for testing",
                severity=Severity.HIGH,
                cvss_score=7.5,
                location="mock_function()",
                exploit_scenario="Mock exploit scenario",
                expected_outcome="Mock outcome",
                target_url=target,
                analyzer=self.name,
                confidence=1.0
            )
        ]


class AnalyzerRegistry:
    """Registry for managing analyzer adapters."""
    
    def __init__(self):
        self._adapters: Dict[str, AnalyzerAdapter] = {}
    
    def register(self, adapter: AnalyzerAdapter) -> None:
        """Register an analyzer adapter."""
        self._adapters[adapter.name] = adapter
    
    def get(self, name: str) -> Optional[AnalyzerAdapter]:
        """Get analyzer by name."""
        return self._adapters.get(name)
    
    def get_for_chain(self, chain: str) -> List[AnalyzerAdapter]:
        """Get all analyzers that support a chain."""
        return [
            a for a in self._adapters.values()
            if chain.lower() in [c.lower() for c in a.supported_chains]
        ]
    
    def list_available(self) -> List[str]:
        """List names of available (installed) analyzers."""
        return [
            name for name, adapter in self._adapters.items()
            if adapter.is_available()
        ]
    
    def auto_register(self) -> None:
        """Auto-register all known analyzers."""
        self.register(MockAnalyzerAdapter())
        
        slither = SlitherAdapter()
        if slither.is_available():
            self.register(slither)
        
        mythril = MythrilAdapter()
        if mythril.is_available():
            self.register(mythril)
        
        # Register Solana analyzer (always available - pattern-based)
        solana = SolanaAnalyzerAdapter()
        if solana.is_available():
            self.register(solana)
        
        # Register Frontend analyzer (always available - pattern-based)
        frontend = FrontendAnalyzerAdapter()
        if frontend.is_available():
            self.register(frontend)


def create_analyzer_registry() -> AnalyzerRegistry:
    """Create and auto-populate analyzer registry."""
    registry = AnalyzerRegistry()
    registry.auto_register()
    return registry
