"""
Immunefi Integration

Provides integration with Immunefi bug bounty platform for
automated vulnerability submission.
"""

import asyncio
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


class SubmissionStatus(str, Enum):
    """Status of bounty submission."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    REWARDED = "rewarded"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


@dataclass
class BountySubmission:
    """Bounty submission to Immunefi."""
    id: str = ""
    bounty_id: str = ""
    vulnerability_id: str = ""
    finding_id: str = ""
    audit_id: str = ""
    workspace_id: str = ""
    title: str = ""
    description: str = ""
    severity: str = ""
    cvss_score: Optional[float] = None
    impact: str = ""
    steps_to_reproduce: str = ""
    poc_code: str = ""
    status: SubmissionStatus = SubmissionStatus.DRAFT
    submitted_at: Optional[str] = None
    reward_amount: Optional[float] = None
    reward_currency: str = "USD"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'bounty_id': self.bounty_id,
            'vulnerability_id': self.vulnerability_id,
            'finding_id': self.finding_id,
            'audit_id': self.audit_id,
            'workspace_id': self.workspace_id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'cvss_score': self.cvss_score,
            'impact': self.impact,
            'steps_to_reproduce': self.steps_to_reproduce,
            'poc_code': self.poc_code,
            'status': self.status.value,
            'submitted_at': self.submitted_at,
            'reward_amount': self.reward_amount,
            'reward_currency': self.reward_currency,
            'metadata': self.metadata,
        }


@dataclass
class ImmunefiConfig:
    """Configuration for Immunefi API."""
    api_key: str = ""
    api_secret: str = ""
    base_url: str = "https://immunefi.com/api"
    webhook_secret: str = ""
    timeout: int = 30
    max_retries: int = 3


class ImmunefiClient:
    """
    Client for Immunefi API integration.
    
    Usage:
        client = ImmunefiClient(config)
        
        submission = await client.submit_finding(
            bounty_id="123",
            finding= Vulnerability(...),
        )
    """
    
    SEVERITY_MAP = {
        'CRITICAL': 'critical',
        'HIGH': 'high',
        'MEDIUM': 'medium',
        'LOW': 'low',
        'INFO': 'informational',
    }
    
    def __init__(self, config: ImmunefiConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
    
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
    
    def _sign_request(self, method: str, path: str, body: str = "") -> str:
        """Sign API request with HMAC-SHA256."""
        timestamp = str(int(time.time()))
        message = f"{method}{path}{body}{timestamp}"
        
        signature = hmac.new(
            self.config.api_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        async def _request return signature
    
   (
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make authenticated API request."""
        session = await self._get_session()
        
        url = f"{self.config.base_url}{path}"
        body = json.dumps(data) if data else ""
        
        headers = {
            'Content-Type': 'application/json',
            'X-Api-Key': self.config.api_key,
            'X-Timestamp': str(int(time.time())),
        }
        
        signature = self._sign_request(method, path, body)
        headers['X-Signature'] = signature
        
        for attempt in range(self.config.max_retries):
            try:
                async with session.request(
                    method,
                    url,
                    data=body,
                    headers=headers,
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error = await response.text()
                        logger.error(f"Immunefi API error: {response.status} - {error}")
                        return {'error': error, 'status': response.status}
            except asyncio.TimeoutError:
                logger.error(f"Timeout on attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Request failed: {e}")
        
        return {'error': 'Max retries exceeded'}
    
    async def get_bounties(self) -> List[Dict[str, Any]]:
        """Get list of available bounties."""
        result = await self._request('GET', '/bounties/')
        return result.get('results', [])
    
    async def get_bounty(self, bounty_id: str) -> Dict[str, Any]:
        """Get bounty details."""
        return await self._request('GET', f'/bounties/{bounty_id}/')
    
    async def submit_finding(
        self,
        bounty_id: str,
        title: str,
        description: str,
        severity: str,
        steps_to_reproduce: str,
        impact: str,
        poc_code: str = "",
        cvss_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Submit a vulnerability finding."""
        data = {
            'title': title,
            'description': description,
            'vulnerability_type': self.SEVERITY_MAP.get(severity, 'medium'),
            'severity': self.SEVERITY_MAP.get(severity, 'medium'),
            'steps_to_reproduce': steps_to_reproduce,
            'impact': impact,
            'proof_of_concept': poc_code,
        }
        
        if cvss_score:
            data['cvss_score'] = cvss_score
        
        return await self._request('POST', f'/bounties/{bounty_id}/submissions/', data)
    
    async def get_submission_status(self, submission_id: str) -> Dict[str, Any]:
        """Get submission status."""
        return await self._request('GET', f'/submissions/{submission_id}/')
    
    async def upload_poc(self, submission_id: str, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Upload proof of concept file."""
        session = await self._get_session()
        
        url = f"{self.config.base_url}/submissions/{submission_id}/poc/"
        
        form = aiohttp.FormData()
        form.add_field('file', file_data, filename=filename, content_type='application/octet-stream')
        
        headers = {
            'X-Api-Key': self.config.api_key,
        }
        
        async with session.post(url, data=form, headers=headers) as response:
            return await response.json()
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook payload signature."""
        if not self.config.webhook_secret:
            return False
        
        expected = hmac.new(
            self.config.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)


class ImmunefiService:
    """
    High-level service for Immunefi integration.
    
    Handles submission workflow, status tracking, and rewards.
    """
    
    def __init__(self, client: ImmunefiClient):
        self.client = client
        self._submissions: Dict[str, BountySubmission] = {}
    
    async def submit_finding_from_audit(
        self,
        bounty_id: str,
        audit_id: str,
        workspace_id: str,
        vulnerability: Dict[str, Any],
        exploit_code: str = "",
    ) -> Optional[BountySubmission]:
        """Submit a finding from audit results."""
        
        submission = BountySubmission(
            bounty_id=bounty_id,
            finding_id=vulnerability.get('id', ''),
            audit_id=audit_id,
            workspace_id=workspace_id,
            title=vulnerability.get('title', ''),
            description=vulnerability.get('description', ''),
            severity=vulnerability.get('severity', 'MEDIUM'),
            cvss_score=vulnerability.get('cvss_score'),
            impact=vulnerability.get('impact', vulnerability.get('expected_outcome', '')),
            steps_to_reproduce=vulnerability.get('exploit_scenario', ''),
            poc_code=exploit_code,
            status=SubmissionStatus.DRAFT,
        )
        
        try:
            result = await self.client.submit_finding(
                bounty_id=bounty_id,
                title=submission.title,
                description=submission.description,
                severity=submission.severity,
                steps_to_reproduce=submission.steps_to_reproduce,
                impact=submission.impact,
                poc_code=submission.poc_code,
                cvss_score=submission.cvss_score,
            )
            
            if 'error' not in result:
                submission.id = result.get('id', '')
                submission.status = SubmissionStatus.SUBMITTED
                submission.submitted_at = datetime.utcnow().isoformat()
                
                self._submissions[submission.id] = submission
                logger.info(f"Submitted finding to Immunefi: {submission.id}")
                return submission
            else:
                logger.error(f"Failed to submit: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error submitting to Immunefi: {e}")
        
        return None
    
    async def check_submission_status(self, submission_id: str) -> Optional[SubmissionStatus]:
        """Check status of a submission."""
        try:
            result = await self.client.get_submission_status(submission_id)
            
            if 'error' not in result:
                status = result.get('status', '')
                return SubmissionStatus(status)
                
        except Exception as e:
            logger.error(f"Error checking status: {e}")
        
        return None
    
    async def process_webhook(self, payload: Dict[str, Any], signature: str) -> Optional[BountySubmission]:
        """Process webhook from Immunefi."""
        
        if not self.client.verify_webhook_signature(json.dumps(payload), signature):
            logger.warning("Invalid webhook signature")
            return None
        
        event_type = payload.get('event_type', '')
        submission_id = payload.get('submission_id', '')
        
        if event_type == 'submission_status_changed':
            status = payload.get('new_status', '')
            reward = payload.get('reward_amount', 0)
            
            if submission_id in self._submissions:
                submission = self._submissions[submission_id]
                submission.status = SubmissionStatus(status)
                submission.reward_amount = reward
                
                logger.info(f"Submission {submission_id} status: {status}, reward: {reward}")
                return submission
        
        return None
    
    def get_submission(self, submission_id: str) -> Optional[BountySubmission]:
        """Get submission by ID."""
        return self._submissions.get(submission_id)
    
    def get_workspace_submissions(self, workspace_id: str) -> List[BountySubmission]:
        """Get all submissions for a workspace."""
        return [
            s for s in self._submissions.values()
            if s.workspace_id == workspace_id
        ]
    
    def get_workspace_rewards(self, workspace_id: str) -> float:
        """Get total rewards for a workspace."""
        return sum(
            s.reward_amount or 0
            for s in self._submissions.values()
            if s.workspace_id == workspace_id and s.status == SubmissionStatus.REWARDED
        )


_immunefi_client: Optional[ImmunefiClient] = None
_immunefi_service: Optional[ImmunefiService] = None


def get_immunefi_client(config: Optional[ImmunefiConfig] = None) -> ImmunefiClient:
    """Get Immunefi client instance."""
    global _immunefi_client
    if _immunefi_client is None:
        _immunefi_client = ImmunefiClient(config or ImmunefiConfig())
    return _immunefi_client


def get_immunefi_service() -> ImmunefiService:
    """Get Immunefi service instance."""
    global _immunefi_service
    if _immunefi_service is None:
        _immunefi_service = ImmunefiService(get_immunefi_client())
    return _immunefi_service
