"""Typed values shared by the project control services.

The CLI is intentionally a renderer over these ordinary Python values.  Keeping
the service layer free of Cyclopts makes it usable from tests, hooks, and future
project-specific adapters without manufacturing a second runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

GoalStatus = Literal["active", "passed", "exhausted"]
ContractSource = Literal["explicit", "feature-map", "spec"]
CheckStatus = Literal["pass", "warn", "fail"]
EvidenceVerdict = Literal["VERIFIED", "NOT VERIFIED", "INCONCLUSIVE"]


@dataclass(frozen=True, slots=True)
class SpecArtifactDigest:
    """One immutable native-spec artifact bound into a verifier contract."""

    path: str
    sha256: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpecArtifactDigest:
        if not isinstance(data, dict) or set(data) != {"path", "sha256"}:
            raise TypeError("spec artifact digest must contain exactly path and sha256")
        if type(data["path"]) is not str or type(data["sha256"]) is not str:
            raise TypeError("spec artifact path and sha256 must be strings")
        return cls(path=data["path"], sha256=data["sha256"])


@dataclass(frozen=True, slots=True)
class CommandSpec:
    """A shell-free command plus provenance for an executable contract."""

    argv: tuple[str, ...]
    display: str
    source: ContractSource
    feature: str | None = None
    spec: str | None = None
    spec_artifacts: tuple[SpecArtifactDigest, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["argv"] = list(self.argv)
        if self.spec_artifacts:
            data["spec_artifacts"] = [item.to_dict() for item in self.spec_artifacts]
        else:
            # Preserve schema-2 digests for non-spec goal records created before
            # native-spec content binding was introduced.
            data.pop("spec_artifacts")
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CommandSpec:
        if not isinstance(data, dict):
            raise TypeError("command contract must be an object")
        argv = data["argv"]
        if not isinstance(argv, list) or not argv or not all(type(item) is str for item in argv):
            raise TypeError("command argv must be a non-empty list of strings")
        display = data["display"]
        source = data["source"]
        if type(display) is not str:
            raise TypeError("command display must be a string")
        if source not in {"explicit", "feature-map", "spec"}:
            raise ValueError("command source is invalid")
        feature = data.get("feature")
        spec = data.get("spec")
        if feature is not None and type(feature) is not str:
            raise TypeError("command feature provenance must be a string or null")
        if spec is not None and type(spec) is not str:
            raise TypeError("command spec provenance must be a string or null")
        spec_artifacts = data.get("spec_artifacts", [])
        if not isinstance(spec_artifacts, list):
            raise TypeError("command spec artifacts must be a list")
        return cls(
            argv=tuple(argv),
            display=display,
            source=source,
            feature=feature,
            spec=spec,
            spec_artifacts=tuple(SpecArtifactDigest.from_dict(item) for item in spec_artifacts),
        )


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Bounded, serializable evidence from one verifier attempt."""

    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False
    truncated: bool = False
    error: str | None = None
    started_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationResult:
        if not isinstance(data, dict):
            raise TypeError("verification result must be an object")
        _require_bool(data, "passed")
        _require_int(data, "exit_code")
        _require_int(data, "duration_ms")
        for key in ("stdout", "stderr"):
            if key in data and type(data[key]) is not str:
                raise TypeError(f"verification {key} must be a string")
        for key in ("timed_out", "truncated"):
            if key in data and type(data[key]) is not bool:
                raise TypeError(f"verification {key} must be a boolean")
        for key in ("error", "started_at"):
            if key in data and data[key] is not None and type(data[key]) is not str:
                raise TypeError(f"verification {key} must be a string or null")
        return cls(
            passed=data["passed"],
            exit_code=data["exit_code"],
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            duration_ms=data["duration_ms"],
            timed_out=data.get("timed_out", False),
            truncated=data.get("truncated", False),
            error=data.get("error"),
            started_at=data.get("started_at"),
        )


@dataclass(slots=True)
class GoalState:
    """Durable state for the current-session verified-goal compatibility seam."""

    schema_version: int
    goal_id: str
    objective: str
    status: GoalStatus
    contract: CommandSpec
    contract_digest: str
    attempt_count: int
    max_attempts: int
    created_at: str
    updated_at: str
    last_result: VerificationResult | None = None
    history: list[VerificationResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "goal_id": self.goal_id,
            "objective": self.objective,
            "status": self.status,
            "contract": self.contract.to_dict(),
            "contract_digest": self.contract_digest,
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_result": self.last_result.to_dict() if self.last_result else None,
            "history": [result.to_dict() for result in self.history],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GoalState:
        if not isinstance(data, dict):
            raise TypeError("goal state must be an object")
        for key in ("schema_version", "attempt_count", "max_attempts"):
            _require_int(data, key)
        for key in (
            "goal_id",
            "objective",
            "status",
            "contract_digest",
            "created_at",
            "updated_at",
        ):
            if type(data[key]) is not str:
                raise TypeError(f"goal {key} must be a string")
        history = data.get("history", [])
        if not isinstance(history, list):
            raise TypeError("goal history must be a list")
        last_result = data.get("last_result")
        return cls(
            schema_version=data["schema_version"],
            goal_id=data["goal_id"],
            objective=data["objective"],
            status=data["status"],
            contract=CommandSpec.from_dict(data["contract"]),
            contract_digest=data["contract_digest"],
            attempt_count=data["attempt_count"],
            max_attempts=data["max_attempts"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            last_result=(
                VerificationResult.from_dict(last_result) if last_result is not None else None
            ),
            history=[VerificationResult.from_dict(item) for item in history],
        )


def _require_bool(data: dict[str, Any], key: str) -> None:
    if type(data[key]) is not bool:
        raise TypeError(f"{key} must be a boolean")


def _require_int(data: dict[str, Any], key: str) -> None:
    if type(data[key]) is not int:
        raise TypeError(f"{key} must be an integer")


@dataclass(frozen=True, slots=True)
class FeatureSubFeature:
    """One independently nameable behavior within a user-facing feature."""

    identifier: str
    behavior: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FeatureEntrypoint:
    """A user path paired with its exact drive recipe and observable proof."""

    identifier: str
    user_path: str
    drive: str
    observable: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    slug: str
    title: str
    path: str
    behavior: str
    expected_path: str
    command: tuple[str, ...] | None
    related: tuple[str, ...]
    draft: bool
    schema_version: int = 2
    sub_features: tuple[FeatureSubFeature, ...] = ()
    entrypoints: tuple[FeatureEntrypoint, ...] = ()
    gotchas: tuple[str, ...] = ()
    evidence_boundary: str = ""
    cleanup_boundary: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["command"] = list(self.command) if self.command else None
        data["related"] = list(self.related)
        data["sub_features"] = [item.to_dict() for item in self.sub_features]
        data["entrypoints"] = [item.to_dict() for item in self.entrypoints]
        data["gotchas"] = list(self.gotchas)
        return data


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """A workspace-contained artifact pointer with optional content binding."""

    path: str
    sha256: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EvidenceEvent:
    """One bounded public decision/evidence checkpoint; never hidden reasoning."""

    schema_version: int
    sequence: int
    timestamp: str
    requirement: str
    evidence: str
    decision: str
    artifact: EvidenceReference | None
    verification: str
    verdict: EvidenceVerdict

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["artifact"] = self.artifact.to_dict() if self.artifact else None
        return data


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    name: str
    status: CheckStatus
    message: str
    remediation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
