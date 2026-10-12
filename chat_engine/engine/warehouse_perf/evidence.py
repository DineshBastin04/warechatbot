"""
Evidence model — and the V2 extension point for external factors.

Every statement the agent makes is an EvidenceItem with an explicit kind, so
reports can keep these apart:

  observed    — a value read from the workspace database
  calculated  — a comparison computed from observed values (baseline, % change)
  anomaly     — a statistical flag (z-score against historical variation)
  inference   — an interpretation consistent with the data, NOT verified
  unknown     — what the available data cannot establish

V1 produces InternalEvidence only (the workspace's own warehouse database).
ExternalEvidence and CorrelationAnalysis exist so a V2 provider (weather,
traffic, carrier feeds, public events ...) can be attached without changing
the analysis engine: implement ExternalEvidenceProvider.collect() and add it to
EXTERNAL_PROVIDERS. The list is intentionally empty in V1 and the analyzer
never calls anything else external.
"""
from dataclasses import asdict, dataclass, field

KINDS = ("observed", "calculated", "anomaly", "inference", "unknown")
KIND_LABEL = {
    "observed": "Observed fact",
    "calculated": "Calculated comparison",
    "anomaly": "Detected anomaly",
    "inference": "Inferred interpretation",
    "unknown": "Unknown / insufficient evidence",
}


@dataclass
class EvidenceItem:
    kind: str
    statement: str
    metric_id: str = None
    scope: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"unknown evidence kind {self.kind!r}")

    def to_dict(self):
        return asdict(self)


@dataclass
class InternalEvidence:
    source: str = "workspace warehouse database"
    items: list = field(default_factory=list)

    def add(self, kind, statement, metric_id=None, **scope):
        self.items.append(EvidenceItem(kind, statement, metric_id, scope))

    def to_dict(self):
        return {"source": self.source, "items": [i.to_dict() for i in self.items]}


@dataclass
class ExternalEvidence:
    """V2: evidence from a named external provider. Always empty in V1."""
    provider: str
    items: list = field(default_factory=list)

    def to_dict(self):
        return {"provider": self.provider, "items": [i.to_dict() for i in self.items]}


@dataclass
class CorrelationAnalysis:
    """V2: how internal deviations line up with external evidence. Not produced in V1."""
    method: str
    findings: list = field(default_factory=list)


class ExternalEvidenceProvider:
    """V2 interface. collect(workspace_public, analysis_result) -> ExternalEvidence."""
    name = "external"

    def collect(self, workspace_public, analysis_result):
        raise NotImplementedError


EXTERNAL_PROVIDERS = []   # V1: no external data is used.
