"""
Webhooks System

Provides configurable webhook delivery for audit events with
retry logic, signature verification, and delivery logging.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from urllib.parse import urlencode

import aiohttp

logger = logging.getLogger(__name__)


class WebhookEvent(str, Enum):
    """Events that can trigger webhooks."""

    JOB_CREATED = "job.created"
    JOB_STARTED = "job.started"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    PAYMENT_VERIFIED = "payment.verified"
    FINDING_DISCOVERED = "finding.discovered"
    EXPLOIT_GENERATED = "exploit.generated"
    REPORT_GENERATED = "report.generated"
    SUBMISSION_CREATED = "submission.created"


class WebhookStatus(str, Enum):
    """Status of webhook delivery."""

    PENDING = "pending"
    SENDING = "sending"
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class WebhookConfig:
    """Configuration for a webhook."""

    id: str = ""
    url: str = ""
    events: List[WebhookEvent] = field(default_factory=list)
    secret: str = ""
    active: bool = True
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 60
    headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = f"wh_{uuid.uuid4().hex[:12]}"


@dataclass
class WebhookDelivery:
    """Record of a webhook delivery attempt."""

    id: str = ""
    webhook_id: str = ""
    event: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    status: WebhookStatus = WebhookStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    sent_at: Optional[str] = None
    completed_at: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            self.id = f"del_{uuid.uuid4().hex[:16]}"


class WebhookService:
    """
    Webhook delivery service.

    Usage:
        service = WebhookService()

        await service.register_webhook(WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.JOB_COMPLETED],
            secret="mysecret",
        ))

        await service.trigger_event(WebhookEvent.JOB_COMPLETED, {
            "job_id": "123",
            "status": "completed",
        })
    """

    def __init__(self):
        self._webhooks: Dict[str, WebhookConfig] = {}
        self._deliveries: Dict[str, List[WebhookDelivery]] = {}
        self._event_handlers: Dict[WebhookEvent, List[Callable]] = {}

    def register_webhook(self, config: WebhookConfig) -> str:
        """Register a new webhook."""
        self._webhooks[config.id] = config
        logger.info(f"Registered webhook: {config.id} -> {config.url}")
        return config.id

    def update_webhook(self, config: WebhookConfig) -> bool:
        """Update an existing webhook."""
        if config.id in self._webhooks:
            self._webhooks[config.id] = config
            return True
        return False

    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            return True
        return False

    def get_webhook(self, webhook_id: str) -> Optional[WebhookConfig]:
        """Get webhook by ID."""
        return self._webhooks.get(webhook_id)

    def list_webhooks(
        self, event: Optional[WebhookEvent] = None
    ) -> List[WebhookConfig]:
        """List all webhooks, optionally filtered by event."""
        webhooks = []

        for wh in self._webhooks.values():
            if not wh.active:
                continue

            if event is None:
                webhooks.append(wh)
            elif event in wh.events:
                webhooks.append(wh)

        return webhooks

    def get_webhook_deliveries(self, webhook_id: str) -> List[WebhookDelivery]:
        """Get delivery history for a webhook."""
        return self._deliveries.get(webhook_id, [])

    async def trigger_event(
        self,
        event: WebhookEvent,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> List[str]:
        """Trigger webhooks for an event."""
        webhooks = self.list_webhooks(event)

        if not webhooks:
            logger.debug(f"No webhooks registered for event: {event}")
            return []

        delivery_ids = []

        for wh in webhooks:
            delivery = WebhookDelivery(
                webhook_id=wh.id,
                event=event.value,
                payload=payload,
                max_attempts=wh.max_retries + 1,
            )

            if wh.id not in self._deliveries:
                self._deliveries[wh.id] = []

            self._deliveries[wh.id].append(delivery)
            delivery_ids.append(delivery.id)

            asyncio.create_task(self._deliver_webhook(delivery, wh, correlation_id))

        return delivery_ids

    async def _deliver_webhook(
        self,
        delivery: WebhookDelivery,
        webhook: WebhookConfig,
        correlation_id: Optional[str] = None,
    ):
        """Deliver a webhook with retry logic."""

        payload = {
            "id": delivery.id,
            "event": delivery.event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": delivery.payload,
        }

        if correlation_id:
            payload["correlation_id"] = correlation_id

        payload_str = json.dumps(payload)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Agentxploitor-Webhooks/2.0",
            "X-Webhook-Event": delivery.event,
            "X-Webhook-Delivery": delivery.id,
        }

        if webhook.secret:
            signature = hmac.new(
                webhook.secret.encode(),
                payload_str.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        for key, value in webhook.headers.items():
            headers[key] = value

        delivery.status = WebhookStatus.SENDING
        delivery.sent_at = datetime.utcnow().isoformat()

        async with aiohttp.ClientSession() as session:
            for attempt in range(delivery.max_attempts):
                delivery.attempts = attempt + 1

                try:
                    async with session.post(
                        webhook.url,
                        data=payload_str,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=webhook.timeout),
                    ) as response:
                        delivery.response_code = response.status
                        delivery.response_body = await response.text()

                        if 200 <= response.status < 300:
                            delivery.status = WebhookStatus.SUCCESS
                            delivery.completed_at = datetime.utcnow().isoformat()
                            logger.info(f"Webhook delivered: {delivery.id}")
                            break
                        else:
                            delivery.error = f"HTTP {response.status}"

                except asyncio.TimeoutError:
                    delivery.error = "Timeout"
                except Exception as e:
                    delivery.error = str(e)

                if delivery.attempts < delivery.max_attempts:
                    await asyncio.sleep(webhook.retry_delay * (2**attempt))

            if delivery.status != WebhookStatus.SUCCESS:
                delivery.status = WebhookStatus.FAILED
                delivery.completed_at = datetime.utcnow().isoformat()
                logger.error(
                    f"Webhook delivery failed: {delivery.id} - {delivery.error}"
                )

    def register_handler(self, event: WebhookEvent, handler: Callable):
        """Register an in-process event handler."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    async def handle_event(self, event: WebhookEvent, payload: Dict[str, Any]):
        """Handle event with registered handlers."""
        handlers = self._event_handlers.get(event, [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(payload)
                else:
                    handler(payload)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify webhook signature."""
        if not secret:
            return False

        expected = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected}", signature)

    def test_webhook(self, webhook_id: str) -> Optional[WebhookDelivery]:
        """Send a test webhook."""
        webhook = self.get_webhook(webhook_id)

        if not webhook:
            return None

        payload = {
            "event": "test",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"message": "This is a test webhook"},
        }

        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event="test",
            payload=payload,
        )

        if webhook.id not in self._deliveries:
            self._deliveries[webhook.id] = []

        self._deliveries[webhook.id].append(delivery)

        asyncio.create_task(self._deliver_webhook(delivery, webhook))

        return delivery

    def get_delivery_stats(self, webhook_id: str) -> Dict[str, Any]:
        """Get delivery statistics for a webhook."""
        deliveries = self.get_webhook_deliveries(webhook_id)

        if not deliveries:
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "pending": 0,
                "success_rate": 0,
            }

        success = sum(1 for d in deliveries if d.status == WebhookStatus.SUCCESS)
        failed = sum(1 for d in deliveries if d.status == WebhookStatus.FAILED)
        pending = sum(
            1
            for d in deliveries
            if d.status
            in [
                WebhookStatus.PENDING,
                WebhookStatus.SENDING,
            ]
        )

        return {
            "total": len(deliveries),
            "success": success,
            "failed": failed,
            "pending": pending,
            "success_rate": success / len(deliveries) if deliveries else 0,
        }


_webhook_service: Optional[WebhookService] = None


def get_webhook_service() -> WebhookService:
    """Get global webhook service instance."""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service


def create_webhook(url: str, events: List[str], secret: str = "") -> WebhookConfig:
    """Helper to create a webhook config."""
    return WebhookConfig(
        url=url,
        events=[WebhookEvent(e) for e in events],
        secret=secret,
    )
