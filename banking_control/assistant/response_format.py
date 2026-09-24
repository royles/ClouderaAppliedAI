"""Normalize assistant replies for the UI — no chain-of-thought, no pipe tables."""

from __future__ import annotations

import json
import re
from typing import Any

from banking_control.assistant.thinking_suppress import suppress_thinking_markup
from banking_control.llm.openai_tool_parse import strip_model_artifacts

_PLANNING_CUE = re.compile(
    r"\b("
    r"We need to|The user asked|Let's |Thus we|follow the grounding|"
    r"The instruction|We should present|We already called|We'll include"
    r")\b",
    re.IGNORECASE,
)
_STRUCTURE_START = re.compile(
    r"(?:^|\n)(#{1,3}\s+|---+\s*\n|\*\*[A-Z])",
    re.MULTILINE,
)
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}")


def format_testing_guide_payload(guide: dict[str, Any]) -> str:
    if not guide.get("found"):
        return ""
    ctrl = guide["control"]
    lines = [
        f"### {ctrl['control_code']} — {ctrl['control_name']}",
        "",
        (ctrl.get("description") or "").strip(),
        "",
        "### Requirements for Effective status",
        "",
    ]
    for i, item in enumerate(guide.get("effective_status_checklist") or [], 1):
        if i > 12:
            break
        lines.append(f"{i}. {item.get('requirement', '')}")
    refs = guide.get("standards_refs") or []
    if refs:
        lines.extend(
            [
                "",
                "### Regulatory references (external)",
                "",
                "_These links open third-party regulator sites; confirm you are viewing the current version._",
                "",
            ]
        )
        for ref in refs:
            label = ref.get("label") or "Reference"
            url = ref.get("url") or ""
            if url:
                lines.append(f"- [{label}]({url})")
            else:
                lines.append(f"- {label}")
    wh = (guide.get("latest_assessment") or {}).get("evidence_ref")
    if wh:
        lines.extend(["", f"Warehouse assessment evidence ref (if relevant): `{wh}`"])
    wf = guide.get("workflow_suggestions") or []
    if wf:
        lines.extend(["", "### Workflows (create evidence)"])
        for item in wf:
            if item.get("action") == "create" and item.get("proposed_artifact_ref"):
                lines.append(
                    f"- {item.get('label', 'Workflow')}: use **Start workflow** to create "
                    f"`{item['proposed_artifact_ref']}`"
                )
            elif item.get("artifact_ref"):
                lines.append(
                    f"- {item.get('label', 'Workflow')}: `{item['artifact_ref']}` "
                    f"({item.get('status', 'Draft')})"
                )
    lines.extend(
        [
            "",
            "_To run a demo simulation, provide a business unit code (e.g. `RB-EU`) and period end._",
        ]
    )
    return "\n".join(lines).strip()


def append_simulation_section(base: str, wrapped: dict[str, Any]) -> str:
    outputs = (wrapped.get("simulation") or {}).get("outputs") or wrapped.get("simulated_metrics")
    status = wrapped.get("simulated_status") or (outputs or {}).get("status")
    if not status and not outputs:
        return base
    lines = [base, "", "### Simulation (demo)", ""]
    disclaimer = wrapped.get("simulation_disclaimer")
    if disclaimer:
        lines.append(f"_{disclaimer}_")
        lines.append("")
    if status:
        lines.append(f"- **Status:** {status}")
    metrics = wrapped.get("simulated_metrics") or (outputs or {}).get("metrics")
    if isinstance(metrics, dict):
        for key, val in metrics.items():
            lines.append(f"- **{key}:** {val}")
    return "\n".join(lines)


def demote_markdown_tables(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "|" in line and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]):
            header_cells = [c.strip() for c in line.split("|") if c.strip()]
            i += 2
            while i < len(lines) and "|" in lines[i]:
                row = [c.strip() for c in lines[i].split("|") if c.strip()]
                if row:
                    if len(row) >= 2 and header_cells:
                        out.append(f"- **{row[0]}** — {' · '.join(row[1:])}")
                    else:
                        out.append(f"- {' · '.join(row)}")
                i += 1
            continue
        if re.match(r"^\s*\|", line):
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if cells:
                out.append(f"- {' · '.join(cells)}")
            i += 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def trim_planning_monologue(text: str) -> str:
    if not text or len(text) < 180:
        return text
    match = _STRUCTURE_START.search(text)
    if not match or match.start() < 80:
        return text
    prefix = text[: match.start()]
    if len(prefix) > 350 or _PLANNING_CUE.search(prefix):
        return text[match.start() :].lstrip()
    return text


def postprocess_user_visible(text: str) -> str:
    visible = suppress_thinking_markup(text)
    visible = strip_model_artifacts(visible)
    visible = trim_planning_monologue(visible)
    visible = demote_markdown_tables(visible)
    visible = re.sub(r"<br\s*/?>", " ", visible, flags=re.IGNORECASE)
    visible = re.sub(r"\n{3,}", "\n\n", visible).strip()
    return visible


def _parse_tool_payload(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def answer_from_tool_messages(
    messages: list[dict[str, Any]],
    tools_called: list[str],
) -> str:
    guide_payload: dict[str, Any] | None = None
    sim_payload: dict[str, Any] | None = None
    for msg in messages:
        if msg.get("role") != "tool":
            continue
        data = _parse_tool_payload(msg.get("content") or "")
        if isinstance(data, dict) and data.get("found") and "effective_status_checklist" in data:
            guide_payload = data
        if isinstance(data, dict) and data.get("simulation_disclaimer"):
            sim_payload = data
    if "get_control_testing_guide" in tools_called and guide_payload:
        text = format_testing_guide_payload(guide_payload)
        if sim_payload:
            text = append_simulation_section(text, sim_payload)
        return text
    if isinstance(guide_payload, dict) and guide_payload.get("found"):
        return format_testing_guide_payload(guide_payload)
    return ""
