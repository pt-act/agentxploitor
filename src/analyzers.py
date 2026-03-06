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


def create_analyzer_registry() -> AnalyzerRegistry:
    """Create and auto-populate analyzer registry."""
    registry = AnalyzerRegistry()
    registry.auto_register()
    return registry
