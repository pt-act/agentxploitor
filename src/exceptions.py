"""
AgentxploiTor Exceptions

Custom exception hierarchy for proper error handling and propagation.
"""

from typing import Optional, Dict, Any


class AgentError(Exception):
    """Base exception for all AgentxploiTor errors."""
    
    def __init__(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.recoverable = recoverable

    def to_dict(self) -> Dict[str, Any]:
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'context': self.context,
            'recoverable': self.recoverable
        }


class ConfigurationError(AgentError):
    """Raised when agent configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message, 
            context={'config_key': config_key} if config_key else None,
            recoverable=False
        )
        self.config_key = config_key


class ScanError(AgentError):
    """Raised when vulnerability scanning fails."""
    
    def __init__(
        self, 
        message: str, 
        target: Optional[str] = None,
        scan_type: Optional[str] = None,
        recoverable: bool = True
    ):
        super().__init__(
            message,
            context={
                'target': target,
                'scan_type': scan_type
            },
            recoverable=recoverable
        )
        self.target = target
        self.scan_type = scan_type


class AnalyzerError(ScanError):
    """Raised when a specific analyzer fails."""
    
    def __init__(
        self, 
        message: str, 
        analyzer_name: str = None,
        analyzer: str = None,
        target: Optional[str] = None,
        timeout: Optional[int] = None,
        recoverable: bool = True
    ):
        analyzer_val = analyzer_name or analyzer or 'unknown'
        super().__init__(
            message,
            target=target,
            scan_type=analyzer_val,
            recoverable=recoverable
        )
        self.analyzer_name = analyzer_val
        self.analyzer = analyzer_val
        self.timeout = timeout


class ExploitError(AgentError):
    """Raised when exploit generation fails."""
    
    def __init__(
        self, 
        message: str, 
        vulnerability_id: Optional[str] = None,
        technique: Optional[str] = None,
        recoverable: bool = True
    ):
        super().__init__(
            message,
            context={
                'vulnerability_id': vulnerability_id,
                'technique': technique
            },
            recoverable=recoverable
        )
        self.vulnerability_id = vulnerability_id
        self.technique = technique


class SafetyViolationError(ExploitError):
    """Raised when an exploit violates safety constraints."""
    
    def __init__(self, message: str, constraint_violated: str, vulnerability_id: Optional[str] = None):
        super().__init__(
            message,
            vulnerability_id=vulnerability_id,
            recoverable=False
        )
        self.constraint_violated = constraint_violated


class VerificationError(AgentError):
    """Raised when exploit verification fails."""
    
    def __init__(
        self, 
        message: str, 
        vulnerability_id: Optional[str] = None,
        reason: Optional[str] = None,
        recoverable: bool = True
    ):
        super().__init__(
            message,
            context={
                'vulnerability_id': vulnerability_id,
                'reason': reason
            },
            recoverable=recoverable
        )
        self.vulnerability_id = vulnerability_id
        self.reason = reason


class PerceptionError(VerificationError):
    """Raised when browser perception fails."""
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        operation: Optional[str] = None,
        recoverable: bool = True
    ):
        super().__init__(message, recoverable=recoverable)
        self.url = url
        self.operation = operation
        self.context['url'] = url
        self.context['operation'] = operation


class ReportError(AgentError):
    """Raised when report generation or storage fails."""
    
    def __init__(
        self, 
        message: str, 
        report_id: Optional[str] = None,
        recoverable: bool = True
    ):
        super().__init__(message, recoverable=recoverable)
        self.report_id = report_id


class JobStateError(AgentError):
    """Raised when job state transition is invalid."""
    
    def __init__(
        self, 
        message: str, 
        current_state: str,
        attempted_state: str,
        job_id: Optional[str] = None
    ):
        super().__init__(
            message,
            context={
                'current_state': current_state,
                'attempted_state': attempted_state,
                'job_id': job_id
            },
            recoverable=False
        )
        self.current_state = current_state
        self.attempted_state = attempted_state
        self.job_id = job_id


class PaymentError(AgentError):
    """Raised when payment verification fails."""
    
    def __init__(
        self, 
        message: str, 
        tx_hash: Optional[str] = None,
        expected_amount: Optional[str] = None,
        required_confirmations: Optional[int] = None,
        actual_confirmations: Optional[int] = None,
        recoverable: bool = True
    ):
        super().__init__(
            message,
            context={
                'tx_hash': tx_hash,
                'expected_amount': expected_amount,
                'required_confirmations': required_confirmations,
                'actual_confirmations': actual_confirmations,
            },
            recoverable=recoverable
        )
        self.tx_hash = tx_hash
        self.expected_amount = expected_amount
        self.required_confirmations = required_confirmations
        self.actual_confirmations = actual_confirmations


class ValidationError(AgentError):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        provided_value: Optional[Any] = None,
        recoverable: bool = True
    ):
        super().__init__(
            message,
            context={
                'field': field,
                'provided_value': str(provided_value) if provided_value else None,
            },
            recoverable=recoverable
        )
        self.field = field
        self.provided_value = provided_value


class ResourceNotFoundError(AgentError):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        recoverable: bool = False
    ):
        message = f"{resource_type} not found"
        if resource_id:
            message = f"{resource_type} with id '{resource_id}' not found"
        
        super().__init__(
            message,
            context={
                'resource_type': resource_type,
                'resource_id': resource_id,
            },
            recoverable=recoverable
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class TimeoutError(AgentError):
    """Raised when an operation times out."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        recoverable: bool = True
    ):
        super().__init__(
            message,
            context={
                'operation': operation,
                'timeout_seconds': timeout_seconds,
            },
            recoverable=recoverable
        )
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class RateLimitError(AgentError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
        retry_after: Optional[int] = None,
        recoverable: bool = True
    ):
        super().__init__(
            message,
            context={
                'limit': limit,
                'window_seconds': window_seconds,
                'retry_after': retry_after,
            },
            recoverable=recoverable
        )
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after = retry_after
