"""
Tests for AgentxploiTor Analyzer Adapters
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from analyzers import (
    AnalyzerAdapter,
    SlitherAdapter,
    MythrilAdapter,
    MockAnalyzerAdapter,
    AnalyzerRegistry,
    create_analyzer_registry,
)
from models import Severity, Vulnerability
from exceptions import AnalyzerError, ConfigurationError


class TestMockAnalyzerAdapter:
    """Tests for MockAnalyzerAdapter."""
    
    @pytest.mark.asyncio
    async def test_is_available(self):
        adapter = MockAnalyzerAdapter()
        assert adapter.is_available() is True
    
    @pytest.mark.asyncio
    async def test_scan_returns_vulnerabilities(self):
        adapter = MockAnalyzerAdapter()
        vulnerabilities = await adapter.scan("https://example.com")
        
        assert len(vulnerabilities) == 1
        assert vulnerabilities[0].title == "Mock Vulnerability - Missing Authorization"
        assert vulnerabilities[0].severity == Severity.HIGH
        assert vulnerabilities[0].cvss_score == 7.5
        assert vulnerabilities[0].target_url == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_scan_returns_vulnerability_with_analyzer_name(self):
        adapter = MockAnalyzerAdapter()
        vulnerabilities = await adapter.scan("https://example.com")
        
        assert vulnerabilities[0].analyzer == "mock"


class TestSlitherAdapter:
    """Tests for SlitherAdapter."""
    
    def test_name_and_supported_chains(self):
        adapter = SlitherAdapter()
        assert adapter.name == "slither"
        assert "ethereum" in adapter.supported_chains
        assert "base" in adapter.supported_chains
    
    def test_is_available_when_installed(self):
        adapter = SlitherAdapter()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Slither 0.9.0")
            assert adapter.is_available() is True
    
    def test_is_available_when_not_installed(self):
        adapter = SlitherAdapter()
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            assert adapter.is_available() is False
    
    def test_severity_mapping(self):
        adapter = SlitherAdapter()
        
        assert adapter.SEVERITY_MAP["High"] == Severity.HIGH
        assert adapter.SEVERITY_MAP["Medium"] == Severity.MEDIUM
        assert adapter.SEVERITY_MAP["Low"] == Severity.LOW
        assert adapter.SEVERITY_MAP["Informational"] == Severity.INFO
    
    def test_parse_finding(self):
        adapter = SlitherAdapter()
        
        finding = {
            "id": "test-001",
            "check": "Reentrancy",
            "description": "Potential reentrancy vulnerability",
            "impact": "High",
            "confidence": 90,
            "elements": [
                {
                    "name": "withdraw",
                    "source_mapping": {
                        "filename_relative": "contracts/Vault.sol"
                    }
                }
            ]
        }
        
        vuln = adapter._parse_finding(finding, "https://example.com")
        
        assert vuln.id == "SLITHER-test-001"
        assert vuln.title == "Reentrancy"
        assert vuln.severity == Severity.HIGH
        assert vuln.cvss_score == 7.5
        assert "Vault.sol" in vuln.location
        assert vuln.analyzer == "slither"
        assert vuln.confidence == 0.9
    
    def test_estimate_cvss(self):
        adapter = SlitherAdapter()
        
        assert adapter._estimate_cvss(Severity.CRITICAL) == 9.5
        assert adapter._estimate_cvss(Severity.HIGH) == 7.5
        assert adapter._estimate_cvss(Severity.MEDIUM) == 5.0
        assert adapter._estimate_cvss(Severity.LOW) == 3.0
        assert adapter._estimate_cvss(Severity.INFO) == 1.0


class TestMythrilAdapter:
    """Tests for MythrilAdapter."""
    
    def test_name_and_supported_chains(self):
        adapter = MythrilAdapter()
        assert adapter.name == "mythril"
        assert "ethereum" in adapter.supported_chains
    
    def test_is_available_when_installed(self):
        adapter = MythrilAdapter()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Mythril 0.23.0")
            assert adapter.is_available() is True
    
    def test_parse_output(self):
        adapter = MythrilAdapter()
        
        data = {
            "issues": [
                {
                    "swc-id": "SWC-107",
                    "title": "Reentrancy",
                    "description": "Reentrancy vulnerability",
                    "severity": "High",
                    "filename": "contracts/Vault.sol",
                    "code": "call.value(amount)"
                }
            ]
        }
        
        vulnerabilities = adapter._parse_output(data, "https://example.com")
        
        assert len(vulnerabilities) == 1
        assert vulnerabilities[0].id == "MYTHRIL-SWC-107"
        assert vulnerabilities[0].title == "Reentrancy"
        assert vulnerabilities[0].severity == Severity.HIGH
        assert vulnerabilities[0].analyzer == "mythril"


class TestAnalyzerRegistry:
    """Tests for AnalyzerRegistry."""
    
    def test_register_and_get(self):
        registry = AnalyzerRegistry()
        adapter = MockAnalyzerAdapter()
        
        registry.register(adapter)
        
        assert registry.get("mock") == adapter
        assert registry.get("nonexistent") is None
    
    def test_get_for_chain(self):
        registry = AnalyzerRegistry()
        mock = MockAnalyzerAdapter()
        mock.supported_chains = ["ethereum", "solana"]
        
        registry.register(mock)
        
        ethereum_adapters = registry.get_for_chain("ethereum")
        assert mock in ethereum_adapters
        
        bitcoin_adapters = registry.get_for_chain("bitcoin")
        assert mock not in bitcoin_adapters
    
    def test_list_available(self):
        registry = AnalyzerRegistry()
        
        mock = MockAnalyzerAdapter()
        with patch.object(mock, 'is_available', return_value=True):
            registry.register(mock)
            available = registry.list_available()
            assert "mock" in available
    
    def test_auto_register(self):
        registry = AnalyzerRegistry()
        
        with patch.object(SlitherAdapter, 'is_available', return_value=False):
            with patch.object(MythrilAdapter, 'is_available', return_value=False):
                registry.auto_register()
                
                assert "mock" in registry._adapters
                assert "slither" not in registry._adapters
                assert "mythril" not in registry._adapters


class TestCreateAnalyzerRegistry:
    """Tests for create_analyzer_registry factory."""
    
    def test_creates_registry_with_adapters(self):
        registry = create_analyzer_registry()
        
        assert isinstance(registry, AnalyzerRegistry)
        assert "mock" in registry._adapters
