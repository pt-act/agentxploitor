"""
Semantic Safety Analysis

Analyzes exploit payloads for dangerous patterns using AST-based analysis.
Ensures generated exploits are safe and controlled.
"""

import ast
import re
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from enum import Enum

logger = logging.getLogger(__name__)


class SafetyLevel(str, Enum):
    """Safety levels for exploit payloads."""
    SAFE = "safe"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    DANGEROUS = "dangerous"


@dataclass
class SafetyCheck:
    """Result of a safety check."""
    level: SafetyLevel
    passed: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'level': self.level.value,
            'passed': self.passed,
            'issues': self.issues,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'score': self.score,
        }


DANGEROUS_PATTERNS = {
    'network': [
        r'socket\.connect',
        r'requests\.get',
        r'urllib\.request',
        r'fetch\s*\(',
        r'XMLHttpRequest',
        r'eval\s*\(',
        r'Function\s*\(',
    ],
    'filesystem': [
        r'open\s*\([^)]*[\'"]w',
        r'os\.remove',
        r'os\.rmdir',
        r'shutil\.rmtree',
        r'__import__\s*\(\s*[\'"]os',
        r'subprocess\.',
        r'eval\s*\(',
        r'exec\s*\(',
    ],
    'crypto': [
        r'private.*key',
        r'mnemonic',
        r'seed\s*phrase',
        r'wallet\.sign',
        r'account\.privateKey',
    ],
    'exfiltration': [
        r'fetch\s*\([^)]*https?://',
        r'WebSocket\s*\(',
        r'navigator\.sendBeacon',
        r'postMessage',
        r'window\.location',
    ],
}

SAFE_PATTERNS = {
    'read_only': [
        r'console\.log',
        r'console\.warn',
        r'JSON\.stringify',
        r'JSON\.parse',
        r'document\.querySelector',
        r'document\.getElementById',
    ],
    'benign': [
        r'alert\s*\(',
        r'console\.',
        r'throw new Error',
    ],
}


class SemanticSafetyAnalyzer:
    """
    Analyzes exploit payloads for safety.
    
    Uses pattern matching and AST analysis to detect dangerous code.
    """

    def __init__(self, strict: bool = False):
        self._strict = strict
        self._custom_patterns: Dict[str, List[str]] = {}
        self._whitelist: Set[str] = set()

    def analyze(self, payload: str, context: Optional[Dict[str, Any]] = None) -> SafetyCheck:
        """
        Analyze a payload for safety.
        
        Args:
            payload: The exploit payload to analyze
            context: Additional context (target, scope, etc.)
        
        Returns:
            SafetyCheck with safety level and issues
        """
        issues: List[str] = []
        warnings: List[str] = []
        recommendations: List[str] = []
        score = 1.0

        dangerous_matches = self._check_patterns(payload, DANGEROUS_PATTERNS)
        for category, matches in dangerous_matches.items():
            for match in matches:
                issues.append(f"Dangerous pattern [{category}]: {match}")
                score -= 0.2

        safe_matches = self._check_patterns(payload, SAFE_PATTERNS)
        safe_count = sum(len(m) for m in safe_matches.values())
        if safe_count > 0:
            score += 0.05 * safe_count

        if self._looks_like_code(payload):
            ast_issues = self._analyze_ast(payload)
            issues.extend(ast_issues)
            score -= 0.1 * len(ast_issues)

        if context:
            scope_issues = self._check_scope_compliance(payload, context)
            issues.extend(scope_issues)

        score = max(0.0, min(1.0, score))

        level = self._determine_level(score, issues)
        passed = level in (SafetyLevel.SAFE, SafetyLevel.LOW_RISK)

        if score < 0.7:
            recommendations.append("Consider adding safety constraints")
        if score < 0.5:
            recommendations.append("Require manual review before execution")
        if score < 0.3:
            recommendations.append("Do not execute without admin approval")

        return SafetyCheck(
            level=level,
            passed=passed,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            score=score,
        )

    def add_custom_pattern(self, category: str, pattern: str) -> None:
        """Add a custom dangerous pattern."""
        if category not in self._custom_patterns:
            self._custom_patterns[category] = []
        self._custom_patterns[category].append(pattern)

    def add_to_whitelist(self, pattern: str) -> None:
        """Add a pattern to the whitelist."""
        self._whitelist.add(pattern)

    def _check_patterns(
        self,
        payload: str,
        patterns: Dict[str, List[str]],
    ) -> Dict[str, List[str]]:
        """Check payload against patterns."""
        matches: Dict[str, List[str]] = {}

        all_patterns = {**patterns}
        for cat, pats in self._custom_patterns.items():
            if cat in all_patterns:
                all_patterns[cat].extend(pats)
            else:
                all_patterns[cat] = pats

        for category, category_patterns in all_patterns.items():
            for pattern in category_patterns:
                if pattern in self._whitelist:
                    continue
                found = re.findall(pattern, payload, re.IGNORECASE)
                if found:
                    if category not in matches:
                        matches[category] = []
                    matches[category].extend(found)

        return matches

    def _looks_like_code(self, payload: str) -> bool:
        """Check if payload looks like executable code."""
        code_indicators = [
            'function', 'const ', 'let ', 'var ', '=>',
            '{', '}', ';', 'return ', 'if (', 'for (',
        ]
        count = sum(1 for ind in code_indicators if ind in payload)
        return count >= 3

    def _analyze_ast(self, payload: str) -> List[str]:
        """Analyze payload as Python AST for dangerous operations."""
        issues = []

        try:
            tree = ast.parse(payload)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ('eval', 'exec', 'compile'):
                            issues.append(f"Use of {node.func.id}() detected")
                
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ('os', 'subprocess', 'socket', 'requests'):
                            issues.append(f"Import of {alias.name} module")

        except SyntaxError:
            pass

        return issues

    def _check_scope_compliance(
        self,
        payload: str,
        context: Dict[str, Any],
    ) -> List[str]:
        """Check if payload complies with scope restrictions."""
        issues = []

        scope = context.get('scope', '')
        target_url = context.get('target_url', '')

        if 'localhost' in payload.lower() or '127.0.0.1' in payload:
            if 'localhost' not in scope.lower():
                issues.append("Payload targets localhost outside scope")

        url_pattern = r'https?://[^\s\'"]+'
        urls = re.findall(url_pattern, payload)
        for url in urls:
            if target_url and target_url not in url:
                issues.append(f"Payload references out-of-scope URL: {url}")

        return issues

    def _determine_level(self, score: float, issues: List[str]) -> SafetyLevel:
        """Determine safety level from score and issues."""
        if score >= 0.9 and len(issues) == 0:
            return SafetyLevel.SAFE
        elif score >= 0.7:
            return SafetyLevel.LOW_RISK
        elif score >= 0.5:
            return SafetyLevel.MEDIUM_RISK
        elif score >= 0.3:
            return SafetyLevel.HIGH_RISK
        else:
            return SafetyLevel.DANGEROUS


class ExploitTemplateLibrary:
    """Library of safe exploit templates."""

    TEMPLATES = {
        'reentrancy': {
            'pattern': '''
                // Reentrancy check
                const vulnerable = await contract.vulnerableFunction();
                // This template is read-only for verification
                console.log("Vulnerability verified:", vulnerable);
            ''',
            'safety': SafetyLevel.SAFE,
            'description': 'Safe reentrancy verification template',
        },
        'overflow': {
            'pattern': '''
                // Integer overflow check
                const max = ethers.constants.MaxUint256;
                const result = await contract.checkOverflow(max);
                console.log("Overflow check result:", result);
            ''',
            'safety': SafetyLevel.SAFE,
            'description': 'Safe integer overflow verification',
        },
        'access_control': {
            'pattern': '''
                // Access control verification
                const owner = await contract.owner();
                const caller = await signer.getAddress();
                console.log("Owner:", owner, "Caller:", caller);
            ''',
            'safety': SafetyLevel.SAFE,
            'description': 'Safe access control verification',
        },
        'xss': {
            'pattern': '''
                // XSS verification (read-only)
                const input = "<script>alert('XSS')</script>";
                const element = document.querySelector('#output');
                // Only verify, don't execute
                console.log("XSS test payload prepared");
            ''',
            'safety': SafetyLevel.LOW_RISK,
            'description': 'XSS verification template',
        },
    }

    @classmethod
    def get_template(cls, name: str) -> Optional[Dict[str, Any]]:
        """Get a template by name."""
        return cls.TEMPLATES.get(name)

    @classmethod
    def list_templates(cls) -> List[str]:
        """List available template names."""
        return list(cls.TEMPLATES.keys())

    @classmethod
    def get_safe_template(cls, name: str) -> Optional[str]:
        """Get a safe template (only SAFE level)."""
        template = cls.TEMPLATES.get(name)
        if template and template['safety'] == SafetyLevel.SAFE:
            return template['pattern']
        return None


_safety_analyzer: Optional[SemanticSafetyAnalyzer] = None


def get_safety_analyzer() -> SemanticSafetyAnalyzer:
    """Get global safety analyzer instance."""
    global _safety_analyzer
    if _safety_analyzer is None:
        _safety_analyzer = SemanticSafetyAnalyzer()
    return _safety_analyzer


def analyze_payload_safety(
    payload: str,
    context: Optional[Dict[str, Any]] = None,
) -> SafetyCheck:
    """Convenience function to analyze payload safety."""
    return get_safety_analyzer().analyze(payload, context)
