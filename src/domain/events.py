"""
Domain Events - Event Bus and Webhooks

Event bus for publishing and subscribing to domain events.
Webhook integration for external system notifications.
"""

import asyncio
import json
import logging
import hashlib
import hmac
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Set
from enum import Enum
import aiohttp

from domain.event_sourcing import DomainEvent, EventType

logger = logging.getLogger(__name__)


# ============================================================================
# Event Bus
# ============================================================================

class EventBus:
    """
    In-process event bus for domain events.
    
    Features:
    - Synchronous and async handlers
    - Handler priorities
    - Error isolation (one handler failure doesn't affect others)
    - Handler registration by event type
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[tuple]] = {}  # event_type -> [(priority, handler)]
        self._global_handlers: List[tuple] = []  # [(priority, handler)]
        self._lock = asyncio.Lock()
    
    def subscribe(
        self,
        handler: Callable,
        event_type: Optional[str] = None,
        priority: int = 0,
    ) -> None:
        """
        Subscribe to events.
        
        Args:
            handler: Callable that receives DomainEvent
            event_type: Specific event type, or None for all events
            priority: Higher priority handlers run first
        """
        if event_type:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append((priority, handler))
            self._handlers[event_type].sort(key=lambda x: -x[0])
        else:
            self._global_handlers.append((priority, handler))
            self._global_handlers.sort(key=lambda x: -x[0])
        
        logger.debug(f"Subscribed handler to {event_type or 'all events'}")
    
    def unsubscribe(self, handler: Callable, event_type: Optional[str] = None) -> bool:
        """Unsubscribe a handler."""
        if event_type:
            if event_type in self._handlers:
                for i, (_, h) in enumerate(self._handlers[event_type]):
                    if h == handler:
                        self._handlers[event_type].pop(i)
                        return True
        else:
            for i, (_, h) in enumerate(self._global_handlers):
                if h == handler:
                    self._global_handlers.pop(i)
                    return True
        return False
    
    async def publish(self, event: DomainEvent) -> List[Exception]:
        """
        Publish event to all subscribers.
        
        Returns list of exceptions from failed handlers.
        """
        errors = []
        
        handlers_to_call = []
        
        for priority, handler in self._global_handlers:
            handlers_to_call.append(handler)
        
        if event.event_type in self._handlers:
            for priority, handler in self._handlers[event.event_type]:
                handlers_to_call.append(handler)
        
        for handler in handlers_to_call:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
                errors.append(e)
        
        return errors
    
    async def publish_batch(self, events: List[DomainEvent]) -> Dict[str, List[Exception]]:
        """Publish multiple events."""
        results = {}
        for event in events:
            results[event.event_id] = await self.publish(event)
        return results
    
    def subscriber_count(self, event_type: Optional[str] = None) -> int:
        """Count subscribers."""
        count = len(self._global_handlers)
        if event_type and event_type in self._handlers:
            count += len(self._handlers[event_type])
        return count


# ============================================================================
# Webhook Configuration
# ============================================================================

@dataclass
class WebhookConfig:
    """Webhook endpoint configuration."""
    id: str
    url: str
    secret: Optional[str] = None
    event_types: List[str] = field(default_factory=list)  # Empty = all events
    active: bool = True
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    retry_count: int = 3
    
    def should_send(self, event_type: str) -> bool:
        """Check if this webhook should receive the event."""
        if not self.active:
            return False
        if not self.event_types:
            return True
        return event_type in self.event_types


@dataclass
class WebhookDelivery:
    """Record of webhook delivery attempt."""
    id: str
    webhook_id: str
    event_type: str
    event_id: str
    url: str
    payload: Dict[str, Any]
    status_code: Optional[int] = None
    response: Optional[str] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    success: bool = False
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'webhook_id': self.webhook_id,
            'event_type': self.event_type,
            'event_id': self.event_id,
            'url': self.url,
            'status_code': self.status_code,
            'error': self.error,
            'duration_ms': self.duration_ms,
            'success': self.success,
            'timestamp': self.timestamp,
        }


class WebhookRegistry:
    """
    Registry for webhook configurations.
    
    Manages webhook endpoints and their event subscriptions.
    """
    
    def __init__(self):
        self._webhooks: Dict[str, WebhookConfig] = {}
    
    def register(self, webhook: WebhookConfig) -> None:
        """Register a webhook."""
        self._webhooks[webhook.id] = webhook
        logger.info(f"Registered webhook: {webhook.id} -> {webhook.url}")
    
    def unregister(self, webhook_id: str) -> bool:
        """Unregister a webhook."""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            return True
        return False
    
    def get(self, webhook_id: str) -> Optional[WebhookConfig]:
        """Get webhook by ID."""
        return self._webhooks.get(webhook_id)
    
    def get_for_event(self, event_type: str) -> List[WebhookConfig]:
        """Get all webhooks that should receive this event."""
        return [
            wh for wh in self._webhooks.values()
            if wh.should_send(event_type)
        ]
    
    def list_all(self) -> List[WebhookConfig]:
        """List all webhooks."""
        return list(self._webhooks.values())


# ============================================================================
# Webhook Sender
# ============================================================================

class WebhookSender:
    """
    Sends webhooks to external endpoints.
    
    Features:
    - Signature generation for security
    - Retry with exponential backoff
    - Delivery logging
    - Timeout handling
    """
    
    SIGNATURE_HEADER = "X-Agentxploitor-Signature"
    EVENT_TYPE_HEADER = "X-Agentxploitor-Event"
    TIMESTAMP_HEADER = "X-Agentxploitor-Timestamp"
    
    def __init__(self, timeout: float = 30.0, max_retries: int = 3):
        self._timeout = timeout
        self._max_retries = max_retries
        self._delivery_log: List[WebhookDelivery] = []
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def send(
        self,
        webhook: WebhookConfig,
        event: DomainEvent,
    ) -> WebhookDelivery:
        """Send event to webhook endpoint."""
        import uuid
        
        delivery_id = f"del-{uuid.uuid4().hex[:16]}"
        payload = self._build_payload(event)
        
        delivery = WebhookDelivery(
            id=delivery_id,
            webhook_id=webhook.id,
            event_type=event.event_type,
            event_id=event.event_id,
            url=webhook.url,
            payload=payload,
        )
        
        headers = self._build_headers(webhook, event, payload)
        headers.update(webhook.headers)
        
        for attempt in range(webhook.retry_count):
            try:
                if self._session is None:
                    self._session = aiohttp.ClientSession()
                
                start = asyncio.get_event_loop().time()
                
                async with self._session.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=webhook.timeout),
                ) as response:
                    delivery.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
                    delivery.status_code = response.status
                    
                    if response.status >= 200 and response.status < 300:
                        delivery.success = True
                        delivery.response = await response.text()[:1000]
                        logger.info(f"Webhook {webhook.id} delivered: {response.status}")
                    else:
                        delivery.error = f"HTTP {response.status}"
                        logger.warning(f"Webhook {webhook.id} failed: {response.status}")
                    
                    break
                    
            except asyncio.TimeoutError:
                delivery.error = "Timeout"
                logger.warning(f"Webhook {webhook.id} timeout (attempt {attempt + 1})")
                
            except aiohttp.ClientError as e:
                delivery.error = str(e)
                logger.warning(f"Webhook {webhook.id} error (attempt {attempt + 1}): {e}")
                
            except Exception as e:
                delivery.error = str(e)
                logger.error(f"Webhook {webhook.id} unexpected error: {e}")
                break
            
            if attempt < webhook.retry_count - 1:
                await asyncio.sleep(2 ** attempt)
        
        self._delivery_log.append(delivery)
        
        if len(self._delivery_log) > 1000:
            self._delivery_log = self._delivery_log[-500:]
        
        return delivery
    
    def _build_payload(self, event: DomainEvent) -> Dict[str, Any]:
        """Build webhook payload."""
        return {
            'event_id': event.event_id,
            'event_type': event.event_type,
            'aggregate_type': event.aggregate_type,
            'aggregate_id': event.aggregate_id,
            'timestamp': event.timestamp,
            'payload': event.payload,
            'metadata': event.metadata,
        }
    
    def _build_headers(
        self,
        webhook: WebhookConfig,
        event: DomainEvent,
        payload: Dict[str, Any],
    ) -> Dict[str, str]:
        """Build request headers including signature."""
        headers = {
            'Content-Type': 'application/json',
            self.EVENT_TYPE_HEADER: event.event_type,
            self.TIMESTAMP_HEADER: event.timestamp,
        }
        
        if webhook.secret:
            signature = self._compute_signature(webhook.secret, payload)
            headers[self.SIGNATURE_HEADER] = signature
        
        return headers
    
    def _compute_signature(self, secret: str, payload: Dict[str, Any]) -> str:
        """Compute HMAC signature for payload."""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"
    
    async def close(self) -> None:
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    def get_delivery_log(self, limit: int = 100) -> List[WebhookDelivery]:
        """Get recent delivery records."""
        return self._delivery_log[-limit:]


# ============================================================================
# Event Publisher
# ============================================================================

class EventPublisher:
    """
    Central event publisher that coordinates event bus and webhooks.
    
    Usage:
        publisher = EventPublisher()
        publisher.register_webhook(webhook_config)
        
        await publisher.publish(event)
    """
    
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        webhook_registry: Optional[WebhookRegistry] = None,
        webhook_sender: Optional[WebhookSender] = None,
    ):
        self._event_bus = event_bus or EventBus()
        self._webhook_registry = webhook_registry or WebhookRegistry()
        self._webhook_sender = webhook_sender or WebhookSender()
    
    def subscribe(self, handler: Callable, event_type: Optional[str] = None) -> None:
        """Subscribe to events on the event bus."""
        self._event_bus.subscribe(handler, event_type)
    
    def register_webhook(self, webhook: WebhookConfig) -> None:
        """Register a webhook endpoint."""
        self._webhook_registry.register(webhook)
    
    async def publish(self, event: DomainEvent) -> Dict[str, Any]:
        """
        Publish event to event bus and webhooks.
        
        Returns summary of delivery results.
        """
        results = {
            'event_id': event.event_id,
            'event_type': event.event_type,
            'bus_errors': [],
            'webhooks': [],
        }
        
        bus_errors = await self._event_bus.publish(event)
        results['bus_errors'] = [str(e) for e in bus_errors]
        
        webhooks = self._webhook_registry.get_for_event(event.event_type)
        
        webhook_tasks = [
            self._webhook_sender.send(webhook, event)
            for webhook in webhooks
        ]
        
        if webhook_tasks:
            deliveries = await asyncio.gather(*webhook_tasks, return_exceptions=True)
            
            for delivery in deliveries:
                if isinstance(delivery, Exception):
                    results['webhooks'].append({
                        'success': False,
                        'error': str(delivery),
                    })
                else:
                    results['webhooks'].append(delivery.to_dict())
        
        return results
    
    async def close(self) -> None:
        """Cleanup resources."""
        await self._webhook_sender.close()


# ============================================================================
# Pre-configured Webhooks
# ============================================================================

def create_slack_webhook(
    webhook_id: str,
    slack_url: str,
    event_types: Optional[List[str]] = None,
) -> WebhookConfig:
    """Create a Slack webhook configuration."""
    return WebhookConfig(
        id=webhook_id,
        url=slack_url,
        event_types=event_types or [],
        headers={'Content-Type': 'application/json'},
    )


def create_discord_webhook(
    webhook_id: str,
    discord_url: str,
    event_types: Optional[List[str]] = None,
) -> WebhookConfig:
    """Create a Discord webhook configuration."""
    return WebhookConfig(
        id=webhook_id,
        url=discord_url,
        event_types=event_types or [],
        headers={'Content-Type': 'application/json'},
    )


def create_generic_webhook(
    webhook_id: str,
    url: str,
    secret: Optional[str] = None,
    event_types: Optional[List[str]] = None,
) -> WebhookConfig:
    """Create a generic webhook configuration."""
    return WebhookConfig(
        id=webhook_id,
        url=url,
        secret=secret,
        event_types=event_types or [],
    )


# ============================================================================
# Singleton instances
# ============================================================================

_event_bus: Optional[EventBus] = None
_webhook_registry: Optional[WebhookRegistry] = None
_webhook_sender: Optional[WebhookSender] = None
_event_publisher: Optional[EventPublisher] = None


def get_event_bus() -> EventBus:
    """Get global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def get_webhook_registry() -> WebhookRegistry:
    """Get global webhook registry instance."""
    global _webhook_registry
    if _webhook_registry is None:
        _webhook_registry = WebhookRegistry()
    return _webhook_registry


def get_webhook_sender() -> WebhookSender:
    """Get global webhook sender instance."""
    global _webhook_sender
    if _webhook_sender is None:
        _webhook_sender = WebhookSender()
    return _webhook_sender


def get_event_publisher() -> EventPublisher:
    """Get global event publisher instance."""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher(
            event_bus=get_event_bus(),
            webhook_registry=get_webhook_registry(),
            webhook_sender=get_webhook_sender(),
        )
    return _event_publisher
