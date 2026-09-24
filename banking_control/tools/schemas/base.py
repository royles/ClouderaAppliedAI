from __future__ import annotations

from typing import Any

BASE_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "business_unit_code": {
            "type": "string",
            "description": "Business unit code (e.g. RB-EU, CB-EU).",
        },
        "period_end": {
            "type": "string",
            "format": "date",
            "description": "Assessment or monitoring period end (ISO date).",
        },
        "evidence_refs": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Workpaper or system evidence identifiers.",
        },
        "sample_size": {
            "type": "integer",
            "minimum": 1,
            "description": "Sample size for control test (where applicable).",
        },
        "context": {
            "type": "object",
            "description": "Additional domain-specific attributes.",
            "additionalProperties": True,
        },
    },
    "required": ["business_unit_code"],
    "additionalProperties": False,
}

BASE_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "control_code": {"type": "string"},
        "status": {
            "type": "string",
            "enum": ["Effective", "Partially Effective", "Ineffective", "Not Tested"],
        },
        "summary": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string"},
                    "detail": {"type": "string"},
                },
                "required": ["severity", "detail"],
            },
        },
        "metrics": {
            "type": "object",
            "additionalProperties": {"type": "number"},
        },
        "simulated": {"type": "boolean", "const": True},
    },
    "required": ["control_code", "status", "summary", "findings", "simulated"],
}

SPECIALIZED_INPUTS: dict[str, dict[str, Any]] = {
    "sanctions-screening": {
        "type": "object",
        "properties": {
            **BASE_INPUT_SCHEMA["properties"],
            "context": {
                "type": "object",
                "properties": {
                    "payment_id": {"type": "string"},
                    "amount_eur": {"type": "number", "minimum": 0},
                    "counterparty_country": {"type": "string", "minLength": 2, "maxLength": 3},
                    "channel": {"type": "string"},
                },
                "required": ["payment_id", "amount_eur"],
                "additionalProperties": True,
            },
        },
        "required": ["business_unit_code", "context"],
        "additionalProperties": False,
    },
    "customer-due-diligence": {
        "type": "object",
        "properties": {
            **BASE_INPUT_SCHEMA["properties"],
            "context": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "customer_type": {"type": "string", "enum": ["retail", "corporate"]},
                    "risk_rating": {"type": "string", "enum": ["low", "medium", "high"]},
                },
                "required": ["customer_id", "customer_type"],
                "additionalProperties": True,
            },
        },
        "required": ["business_unit_code", "context"],
        "additionalProperties": False,
    },
    "dual-control": {
        "type": "object",
        "properties": {
            **BASE_INPUT_SCHEMA["properties"],
            "context": {
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "string"},
                    "amount_eur": {"type": "number", "minimum": 0},
                    "maker_user": {"type": "string"},
                    "checker_user": {"type": "string"},
                },
                "required": ["transaction_id", "amount_eur", "maker_user", "checker_user"],
                "additionalProperties": True,
            },
        },
        "required": ["business_unit_code", "context"],
        "additionalProperties": False,
    },
    "transaction-monitoring": {
        "type": "object",
        "properties": {
            **BASE_INPUT_SCHEMA["properties"],
            "context": {
                "type": "object",
                "properties": {
                    "alert_id": {"type": "string"},
                    "scenario_id": {"type": "string"},
                    "amount_eur": {"type": "number"},
                },
                "required": ["alert_id"],
                "additionalProperties": True,
            },
        },
        "required": ["business_unit_code", "context"],
        "additionalProperties": False,
    },
}
