from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProcessEdge:
    source: str
    target: str
    label: str


@dataclass(frozen=True)
class ProcessFlow:
    flow_id: str
    name: str
    description: str
    edges: tuple[ProcessEdge, ...]

    def codes(self) -> set[str]:
        out: set[str] = set()
        for e in self.edges:
            out.add(e.source)
            out.add(e.target)
        return out


# Reference process chains (golden MVP codes) — illustrative DAGs, not exhaustive RCM.
PROCESS_FLOWS: tuple[ProcessFlow, ...] = (
    ProcessFlow(
        flow_id="retail-instant-payment",
        name="Retail instant payment chain",
        description="Onboarding CDD through monitoring, fraud overlay, sanctions, and STR escalation.",
        edges=(
            ProcessEdge("KYC-001", "KYC-003", "Ongoing CDD"),
            ProcessEdge("KYC-003", "AML-005", "Transaction monitoring"),
            ProcessEdge("AML-005", "FRAUD-001", "Fraud overlay"),
            ProcessEdge("FRAUD-001", "AML-003", "Sanctions screening"),
            ProcessEdge("AML-005", "AML-006", "Investigation / STR"),
            ProcessEdge("FRAUD-004", "AML-005", "Mule typologies"),
        ),
    ),
    ProcessFlow(
        flow_id="commercial-wire-release",
        name="Commercial wire release",
        description="Signatory validation, beneficiary checks, dual approval, and payment screening.",
        edges=(
            ProcessEdge("KYC-007", "FRAUD-005", "Beneficiary validation"),
            ProcessEdge("FRAUD-005", "COMM-001", "Dual approval"),
            ProcessEdge("COMM-001", "AML-003", "Sanctions screening"),
            ProcessEdge("KYC-004", "KYC-007", "Commercial periodic review"),
        ),
    ),
    ProcessFlow(
        flow_id="trade-finance-sanctions",
        name="Trade finance & sanctions",
        description="Policy frame, trade screening, and payment sanctions alignment.",
        edges=(
            ProcessEdge("AML-002", "AML-004", "Trade finance screening"),
            ProcessEdge("AML-004", "AML-003", "Payment release alignment"),
            ProcessEdge("COMM-002", "AML-004", "Document examination"),
        ),
    ),
    ProcessFlow(
        flow_id="aml-program-governance",
        name="AML program governance",
        description="Enterprise risk assessment, policy, model validation, and training.",
        edges=(
            ProcessEdge("AML-001", "AML-002", "Policy framework"),
            ProcessEdge("AML-002", "AML-009", "Model / rule validation"),
            ProcessEdge("AML-009", "AML-010", "Training & awareness"),
            ProcessEdge("AML-001", "AML-008", "Correspondent banking DD"),
        ),
    ),
    ProcessFlow(
        flow_id="digital-onboarding",
        name="Digital retail onboarding",
        description="Remote onboarding fraud signals feeding CDD and enhanced monitoring.",
        edges=(
            ProcessEdge("KYC-006", "KYC-001", "Retail CDD activation"),
            ProcessEdge("KYC-001", "KYC-008", "File completeness QA"),
            ProcessEdge("KYC-005", "AML-007", "PEP / EDD path"),
        ),
    ),
)


def _flow_for_control(control_code: str) -> ProcessFlow | None:
    matches = [f for f in PROCESS_FLOWS if control_code in f.codes()]
    if not matches:
        return None
    return max(matches, key=lambda f: len(f.codes()))


def _subgraph_nodes(flow: ProcessFlow, focus_code: str) -> set[str]:
    """Nodes on any path through the focus control (ancestors ∪ descendants ∪ focus)."""
    preds: dict[str, set[str]] = {}
    succs: dict[str, set[str]] = {}
    for e in flow.edges:
        succs.setdefault(e.source, set()).add(e.target)
        preds.setdefault(e.target, set()).add(e.source)
        preds.setdefault(e.source, preds.get(e.source, set()))
        succs.setdefault(e.target, succs.get(e.target, set()))

    ancestors: set[str] = set()
    stack = list(preds.get(focus_code, set()))
    while stack:
        n = stack.pop()
        if n in ancestors:
            continue
        ancestors.add(n)
        stack.extend(preds.get(n, set()))

    descendants: set[str] = set()
    stack = list(succs.get(focus_code, set()))
    while stack:
        n = stack.pop()
        if n in descendants:
            continue
        descendants.add(n)
        stack.extend(succs.get(n, set()))

    return ancestors | descendants | {focus_code}


def _assign_layers(codes: set[str], edges: list[ProcessEdge]) -> dict[str, int]:
    preds: dict[str, set[str]] = {c: set() for c in codes}
    for e in edges:
        if e.source in codes and e.target in codes:
            preds[e.target].add(e.source)
    layers: dict[str, int] = {c: 0 for c in codes if not preds[c]}
    changed = True
    while changed:
        changed = False
        for code in codes:
            if code in layers:
                continue
            if preds[code].issubset(layers.keys()):
                layers[code] = max(layers[p] for p in preds[code]) + 1
                changed = True
    return layers


def build_process_graph(control_code: str) -> dict[str, Any] | None:
    flow = _flow_for_control(control_code)
    if flow is None:
        return None
    codes = _subgraph_nodes(flow, control_code)
    edges = [e for e in flow.edges if e.source in codes and e.target in codes]
    layers = _assign_layers(codes, edges)
    by_layer: dict[int, list[str]] = {}
    for code, layer in layers.items():
        by_layer.setdefault(layer, []).append(code)
    for layer in by_layer:
        by_layer[layer].sort()

    return {
        "flow_id": flow.flow_id,
        "flow_name": flow.name,
        "flow_description": flow.description,
        "focus_control_code": control_code,
        "nodes": [
            {
                "control_code": code,
                "layer": layers[code],
                "layer_index": layers[code],
                "position_in_layer": by_layer[layers[code]].index(code),
                "layer_size": len(by_layer[layers[code]]),
                "is_current": code == control_code,
            }
            for code in sorted(codes, key=lambda c: (layers[c], c))
        ],
        "edges": [
            {"from": e.source, "to": e.target, "label": e.label}
            for e in edges
        ],
    }


def list_flows_for_control(control_code: str) -> list[dict[str, str]]:
    return [
        {"flow_id": f.flow_id, "flow_name": f.name}
        for f in PROCESS_FLOWS
        if control_code in f.codes()
    ]
