"""
REST API v2 Specification and Implementation

Version 2 of the Agentxploitor API with improved design,
pagination, field selection, and comprehensive documentation.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Agentxploitor API",
        "version": "2.0.0",
        "description": """
## Enterprise Security Audit API

Agentxploitor provides a comprehensive API for smart contract security audits.

### Authentication

All endpoints require authentication via API key. Include your API key in the header:
```
Authorization: Bearer YOUR_API_KEY
```

### Rate Limiting

- Standard: 100 requests/minute
- Enterprise: 1000 requests/minute

### Pagination

List endpoints support pagination with `limit` and `offset` parameters.

### Field Selection

Use `fields` parameter to select specific fields and reduce response size.
        """,
        "contact": {
            "name": "Agentxploitor Support",
            "email": "support@agentxploitor.com",
        },
        "license": {
            "name": "Proprietary",
        },
    },
    "servers": [
        {
            "url": "https://api.agentxploitor.com/v2",
            "description": "Production server",
        },
        {
            "url": "https://staging.api.agentxploitor.com/v2",
            "description": "Staging server",
        },
    ],
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "description": "API key authentication",
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
            },
        },
        "schemas": {
            "Job": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "target_url": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": [
                            "pending_payment",
                            "queued",
                            "in_progress",
                            "completed",
                            "failed",
                        ],
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "critical"],
                    },
                    "created_at": {"type": "string", "format": "date-time"},
                    "completed_at": {"type": "string", "format": "date-time"},
                },
            },
            "Finding": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "job_id": {"type": "string"},
                    "title": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"],
                    },
                    "cvss_score": {"type": "number"},
                    "confidence": {"type": "number"},
                    "status": {"type": "string"},
                },
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "message": {"type": "string"},
                    "code": {"type": "string"},
                },
            },
        },
    },
    "security": [
        {"BearerAuth": []},
        {"ApiKeyAuth": []},
    ],
    "paths": {
        "/health": {
            "get": {
                "summary": "Health check",
                "description": "Check API health and dependencies",
                "responses": {
                    "200": {
                        "description": "Health status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string"},
                                        "timestamp": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        "/workspaces": {
            "get": {
                "summary": "List workspaces",
                "description": "Get all workspaces accessible to the authenticated user",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer", "default": 20},
                    },
                    {
                        "name": "offset",
                        "in": "query",
                        "schema": {"type": "integer", "default": 0},
                    },
                    {"name": "fields", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {
                        "description": "List of workspaces",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": {
                                            "type": "array",
                                            "items": {
                                                "$ref": "#/components/schemas/Workspace"
                                            },
                                        },
                                        "meta": {
                                            "$ref": "#/components/schemas/PaginationMeta"
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        "/jobs": {
            "get": {
                "summary": "List jobs",
                "description": "Get all jobs in the workspace",
                "parameters": [
                    {
                        "name": "workspace_id",
                        "in": "query",
                        "schema": {"type": "string"},
                    },
                    {"name": "status", "in": "query", "schema": {"type": "string"}},
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer", "default": 20},
                    },
                    {
                        "name": "offset",
                        "in": "query",
                        "schema": {"type": "integer", "default": 0},
                    },
                    {"name": "fields", "in": "query", "schema": {"type": "string"}},
                    {"name": "sort", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {
                        "description": "List of jobs",
                    },
                },
            },
            "post": {
                "summary": "Create job",
                "description": "Start a new security audit",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"},
                        },
                    },
                },
                "responses": {
                    "201": {
                        "description": "Job created",
                    },
                },
            },
        },
        "/jobs/{id}": {
            "get": {
                "summary": "Get job",
                "description": "Get job details by ID",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                    {"name": "fields", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {
                        "description": "Job details",
                    },
                    "404": {
                        "description": "Job not found",
                    },
                },
            },
        },
        "/jobs/{id}/findings": {
            "get": {
                "summary": "List findings",
                "description": "Get all findings for a job",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                    {"name": "severity", "in": "query", "schema": {"type": "string"}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                    {"name": "offset", "in": "query", "schema": {"type": "integer"}},
                    {"name": "fields", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {
                        "description": "List of findings",
                    },
                },
            },
        },
        "/jobs/{id}/cancel": {
            "post": {
                "summary": "Cancel job",
                "description": "Cancel a running or queued job",
                "responses": {
                    "200": {
                        "description": "Job cancelled",
                    },
                },
            },
        },
        "/jobs/{id}/recover": {
            "post": {
                "summary": "Recover job",
                "description": "Recover a failed or interrupted job from checkpoint",
                "responses": {
                    "200": {
                        "description": "Job recovered",
                    },
                },
            },
        },
        "/findings/{id}": {
            "get": {
                "summary": "Get finding",
                "description": "Get finding details",
                "responses": {
                    "200": {
                        "description": "Finding details",
                    },
                },
            },
            "patch": {
                "summary": "Update finding",
                "description": "Update finding status or assignment",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string"},
                                    "assigned_to": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                "responses": {
                    "200": {
                        "description": "Finding updated",
                    },
                },
            },
        },
        "/findings/{id}/comments": {
            "get": {
                "summary": "List comments",
                "description": "Get comments on a finding",
                "responses": {
                    "200": {
                        "description": "List of comments",
                    },
                },
            },
            "post": {
                "summary": "Add comment",
                "description": "Add a comment to a finding",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "content": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                "responses": {
                    "201": {
                        "description": "Comment created",
                    },
                },
            },
        },
        "/reports/{job_id}": {
            "get": {
                "summary": "Get report",
                "description": "Get audit report for a job",
                "parameters": [
                    {
                        "name": "job_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "format",
                        "in": "query",
                        "schema": {"type": "string", "enum": ["json", "pdf", "html"]},
                    },
                ],
                "responses": {
                    "200": {
                        "description": "Audit report",
                    },
                },
            },
        },
        "/metrics": {
            "get": {
                "summary": "Get metrics",
                "description": "Get workspace metrics",
                "parameters": [
                    {
                        "name": "workspace_id",
                        "in": "query",
                        "schema": {"type": "string"},
                    },
                    {"name": "start_date", "in": "query", "schema": {"type": "string"}},
                    {"name": "end_date", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {
                        "description": "Metrics data",
                    },
                },
            },
        },
        "/costs": {
            "get": {
                "summary": "Get costs",
                "description": "Get cost tracking data",
                "parameters": [
                    {
                        "name": "workspace_id",
                        "in": "query",
                        "schema": {"type": "string"},
                    },
                    {"name": "start_date", "in": "query", "schema": {"type": "string"}},
                    {"name": "end_date", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {
                        "description": "Cost data",
                    },
                },
            },
        },
        "/webhooks": {
            "get": {
                "summary": "List webhooks",
                "description": "List configured webhooks",
                "responses": {
                    "200": {
                        "description": "List of webhooks",
                    },
                },
            },
            "post": {
                "summary": "Create webhook",
                "description": "Register a new webhook",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "url": {"type": "string"},
                                    "events": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "secret": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                "responses": {
                    "201": {
                        "description": "Webhook created",
                    },
                },
            },
        },
        "/webhooks/{id}": {
            "get": {
                "summary": "Get webhook",
                "description": "Get webhook configuration",
                "responses": {
                    "200": {
                        "description": "Webhook details",
                    },
                },
            },
            "patch": {
                "summary": "Update webhook",
                "description": "Update webhook configuration",
                "responses": {
                    "200": {
                        "description": "Webhook updated",
                    },
                },
            },
            "delete": {
                "summary": "Delete webhook",
                "description": "Remove a webhook",
                "responses": {
                    "204": {
                        "description": "Webhook deleted",
                    },
                },
            },
        },
        "/webhooks/{id}/test": {
            "post": {
                "summary": "Test webhook",
                "description": "Send a test webhook",
                "responses": {
                    "200": {
                        "description": "Test sent",
                    },
                },
            },
        },
    },
}


@dataclass
class PaginationMeta:
    """Pagination metadata."""

    total: int
    limit: int
    offset: int
    has_more: bool


@dataclass
class ErrorResponse:
    """Error response schema."""

    error: str
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


def create_error_response(error: str, message: str, code: str = None) -> Dict[str, Any]:
    """Create standardized error response."""
    response = {
        "error": error,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if code:
        response["code"] = code
    return response


def create_success_response(data: Any, meta: Optional[Dict] = None) -> Dict[str, Any]:
    """Create standardized success response."""
    response = {"data": data, "timestamp": datetime.utcnow().isoformat()}
    if meta:
        response["meta"] = meta
    return response
