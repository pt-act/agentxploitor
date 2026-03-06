"""
GitHub Integration

Provides integration with GitHub for PR status checks,
repository scanning, and automated feedback.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

import aiohttp

logger = logging.getLogger(__name__)


class CheckStatus(str, Enum):
    """Status of a check run."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CheckConclusion(str, Enum):
    """Conclusion of a check run."""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class FindingComment:
    """Finding comment for PR."""
    path: str
    line: int
    body: str
    finding_id: str = ""
    severity: str = ""


@dataclass
class GitHubConfig:
    """Configuration for GitHub API."""
    app_id: str = ""
    private_key: str = ""
    webhook_secret: str = ""
    base_url: str = "https://api.github.com"
    timeout: int = 30


@dataclass
class ScanResult:
    """Result of a security scan."""
    audit_id: str
    repository: str
    branch: str
    commit_sha: str
    findings_count: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    summary: str = ""
    report_url: Optional[str] = None


class GitHubClient:
    """
    Client for GitHub API integration.
    
    Usage:
        client = GitHubClient(config)
        
        await client.create_check_run(
            owner="org",
            repo="contract",
            sha="abc123",
            status="in_progress",
        )
    """
    
    def __init__(self, config: GitHubConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._installation_token: Optional[str] = None
        self._token_expiry: float = 0
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            )
        return self._session
    
    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _get_installation_token(self, installation_id: str) -> str:
        """Get installation access token."""
        if self._installation_token and time.time() < self._token_expiry - 60:
            return self._installation_token
        
        import jwt
        
        now = int(time.time())
        payload = {
            'iss': self.config.app_id,
            'iat': now,
            'exp': now + 600,
        }
        
        token = jwt.encode(payload, self.config.private_key, algorithm='RS256')
        
        session = await self._get_session()
        url = f"{self.config.base_url}/app/installations/{installation_id}/access_tokens"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
        }
        
        async with session.post(url, headers=headers) as response:
            if response.status == 201:
                data = await response.json()
                self._installation_token = data['token']
                self._token_expiry = now + 3600
                return self._installation_token
        
        raise Exception("Failed to get installation token")
    
    async def _request(
        self,
        method: str,
        path: str,
        installation_id: Optional[str] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make authenticated API request."""
        session = await self._get_session()
        
        url = f"{self.config.base_url}{path}"
        
        headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }
        
        if installation_id:
            token = await self._get_installation_token(installation_id)
            headers['Authorization'] = f'Bearer {token}'
        
        body = json.dumps(data) if data else ""
        
        async with session.request(
            method,
            url,
            data=body,
            headers=headers,
        ) as response:
            text = await response.text()
            
            if response.status >= 200 and response.status < 300:
                if response.content_type == 'application/json':
                    return json.loads(text) if text else {}
                return {'success': True}
            else:
                logger.error(f"GitHub API error: {response.status} - {text}")
                return {'error': text, 'status': response.status}
    
    async def create_check_run(
        self,
        owner: str,
        repo: str,
        sha: str,
        name: str = "AgentxploiTor Security Scan",
        status: CheckStatus = CheckStatus.QUEUED,
        conclusion: Optional[CheckConclusion] = None,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        details_url: Optional[str] = None,
        annotations: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Create a check run."""
        data = {
            'name': name,
            'head_sha': sha,
            'status': status.value,
        }
        
        if status == CheckStatus.COMPLETED and conclusion:
            data['conclusion'] = conclusion.value
        
        if title:
            data['output'] = {'title': title, 'summary': summary or ''}
        
        if details_url:
            data['details_url'] = details_url
        
        if annotations:
            data['output'] = data.get('output', {})
            data['output']['annotations'] = annotations[:50]
        
        return await self._request(
            'POST',
            f'/repos/{owner}/{repo}/check-runs',
            data=data,
        )
    
    async def update_check_run(
        self,
        owner: str,
        repo: str,
        check_run_id: int,
        status: CheckStatus = CheckStatus.COMPLETED,
        conclusion: Optional[CheckConclusion] = None,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        details_url: Optional[str] = None,
        annotations: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Update a check run."""
        data = {
            'status': status.value,
        }
        
        if status == CheckStatus.COMPLETED and conclusion:
            data['conclusion'] = conclusion.value
        
        if title:
            data['output'] = {'title': title, 'summary': summary or ''}
        
        if details_url:
            data['details_url'] = details_url
        
        if annotations:
            data['output'] = data.get('output', {})
            data['output']['annotations'] = annotations[:50]
        
        return await self._request(
            'PATCH',
            f'/repos/{owner}/{repo}/check-runs/{check_run_id}',
            data=data,
        )
    
    async def create_pull_request_review(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        event: str = "COMMENT",
        body: Optional[str] = None,
        comments: Optional[List[FindingComment]] = None,
    ) -> Dict[str, Any]:
        """Create a pull request review with findings."""
        data = {
            'event': event,
        }
        
        if body:
            data['body'] = body
        
        if comments:
            data['comments'] = [
                {
                    'path': c.path,
                    'line': c.line,
                    'body': c.body,
                }
                for c in comments
            ]
        
        return await self._request(
            'POST',
            f'/repos/{owner}/{repo}/pulls/{pull_number}/reviews',
            data=data,
        )
    
    async def create_issue_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str,
    ) -> Dict[str, Any]:
        """Create an issue or PR comment."""
        return await self._request(
            'POST',
            f'/repos/{owner}/{repo}/issues/{issue_number}/comments',
            data={'body': body},
        )
    
    async def get_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> Dict[str, Any]:
        """Get pull request details."""
        return await self._request(
            'GET',
            f'/repos/{owner}/{repo}/pulls/{pull_number}',
        )
    
    async def get_commit_files(
        self,
        owner: str,
        repo: str,
        sha: str,
    ) -> List[Dict[str, Any]]:
        """Get files changed in a commit."""
        result = await self._request(
            'GET',
            f'/repos/{owner}/{repo}/commits/{sha}',
        )
        return result.get('files', [])
    
    async def list_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: str = "security-scan.yml",
    ) -> List[Dict[str, Any]]:
        """List workflow runs."""
        result = await self._request(
            'GET',
            f'/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs',
        )
        return result.get('workflow_runs', [])
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook payload signature."""
        if not self.config.webhook_secret:
            return False
        
        expected = hmac.new(
            self.config.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected}", signature)


class GitHubService:
    """
    High-level service for GitHub integration.
    
    Handles security scanning workflow, PR feedback, and status checks.
    """
    
    def __init__(self, client: GitHubClient):
        self.client = client
    
    async def start_security_scan(
        self,
        owner: str,
        repo: str,
        sha: str,
        installation_id: str,
    ) -> Optional[int]:
        """Start a security scan and create check run."""
        
        result = await self.client.create_check_run(
            owner=owner,
            repo=repo,
            sha=sha,
            status=CheckStatus. Scan",
            summaryxploiTor Security title="Agent="QueQUEUED,
            for security analysisued...",
            installation_id=installation        
        if 'error' not in_id,
        )
 result:
            return result.get('id')
        
        return None
    
    async def update_scan_results(
        self,
        owner: str,
        repo: str,
        check_run_id: int,
        scan_result: ScanResult,
        installation_id: str,
    ) -> bool:
        """Update check run with scan results."""
        
        annotations = self._create_annotations(scan_result)
        
        if scan_result.critical_findings > 0 or scan_result.high_findings > 0:
            conclusion = CheckConclusion.FAILURE
        elif scan_result.medium_findings > 0:
            conclusion = CheckConclusion.NEUTRAL
        else:
            conclusion = CheckConclusion.SUCCESS
        
        result = await self.client.update_check_run(
            owner=owner,
            repo=repo,
            check_run_id=check_run_id,
            status=CheckStatus.COMPLETED,
            conclusion=conclusion,
            title=f"Security Scan: {scan_result.findings_count} findings",
            summary=scan_result.summary,
            details_url=scan_result.report_url,
            annotations=annotations,
            installation_id=installation_id,
        )
        
        return 'error' not in result
    
    def _create_annotations(self, scan_result: ScanResult) -> List[Dict]:
        """Create GitHub annotations from scan results."""
        annotations = []
        
        severity_map = {
            'CRITICAL': 'failure',
            'HIGH': 'failure',
            'MEDIUM': 'warning',
            'LOW': 'notice',
        }
        
        return annotations
    
    async def post_findings_as_pr_review(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        scan_result: ScanResult,
        findings: List[Dict[str, Any]],
        installation_id: str,
    ) -> bool:
        """Post findings as PR review comments."""
        
        body = f"""## 🔒 AgentxploiTor Security Scan Results

**Audit ID:** {scan_result.audit_id}
**Findings:** {scan_result.findings_count}

| Severity | Count |
|----------|-------|
| Critical | {scan_result.critical_findings} |
| High | {scan_result.high_findings} |
| Medium | {scan_result.medium_findings} |
| Low | {scan_result.low_findings} |

{f'**Full Report:** {scan_result.report_url}' if scan_result.report_url else ''}
"""
        
        comments = []
        for finding in findings[:10]:
            comments.append(FindingComment(
                path=finding.get('location', 'contracts/Contract.sol'),
                line=finding.get('line', 1),
                body=self._format_finding_comment(finding),
                finding_id=finding.get('id', ''),
                severity=finding.get('severity', ''),
            ))
        
        result = await self.client.create_pull_request_review(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            event="COMMENT",
            body=body,
            comments=comments if comments else None,
        )
        
        return 'error' not in result
    
    def _format_finding_comment(self, finding: Dict[str, Any]) -> str:
        """Format finding as inline comment."""
        severity = finding.get('severity', 'MEDIUM')
        title = finding.get('title', 'Security Finding')
        description = finding.get('description', '')[:200]
        
        return f"""**{severity}:** {title}

{description}"""
    
    async def process_webhook(self, payload: Dict[str, Any], signature: str) -> Optional[Dict]:
        """Process webhook from GitHub."""
        
        if not self.client.verify_webhook_signature(json.dumps(payload), signature):
            logger.warning("Invalid GitHub webhook signature")
            return None
        
        event_type = payload.get('action', '')
        pr_data = payload.get('pull_request', {})
        
        if event_type == 'opened' or event_type == 'synchronize':
            return {
                'event': 'scan_requested',
                'owner': payload.get('repository', {}).get('owner', {}).get('login'),
                'repo': payload.get('repository', {}).get('name'),
                'sha': payload.get('after') or pr_data.get('head', {}).get('sha'),
                'pull_number': pr_data.get('number'),
                'installation_id': payload.get('installation', {}).get('id'),
            }
        
        return None


_github_client: Optional[GitHubClient] = None
_github_service: Optional[GitHubService] = None


def get_github_client(config: Optional[GitHubConfig] = None) -> GitHubClient:
    """Get GitHub client instance."""
    global _github_client
    if _github_client is None:
        _github_client = GitHubClient(config or GitHubConfig())
    return _github_client


def get_github_service() -> GitHubService:
    """Get GitHub service instance."""
    global _github_service
    if _github_service is None:
        _github_service = GitHubService(get_github_client())
    return _github_service
