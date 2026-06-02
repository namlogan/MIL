from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apps.flange_qc_v2.calibration import load_calibration_config
from apps.flange_qc_v2.decision_engine import DecisionResult, evaluate_phase_two_geometry
from apps.flange_qc_v2.domain import ValidationError
from apps.flange_qc_v2.geometry import resolve_geometry_measurements
from apps.flange_qc_v2.product_specs import load_product_specs


@dataclass(frozen=True)
class ReplayFrame:
    frame_id: str
    source_uri: str
    captured_at: str
    measurements: dict[str, Any]

    def __post_init__(self) -> None:
        for field_name in ("frame_id", "source_uri", "captured_at"):
            if not str(getattr(self, field_name)).strip():
                raise ValidationError(f"{field_name} is required")
        if not self.source_uri.startswith("synthetic://"):
            raise ValidationError("frame source_uri must use synthetic://")
        if not isinstance(self.measurements, dict):
            raise ValidationError("frame measurements must be an object")
        resolve_geometry_measurements(self.measurements)

    @classmethod
    def from_payload(cls, payload: Any) -> "ReplayFrame":
        if not isinstance(payload, dict):
            raise ValidationError("frame must be an object")
        for field_name in ("frame_id", "source_uri", "captured_at", "measurements"):
            if field_name not in payload:
                raise ValidationError(f"frame {field_name} is required")
        return cls(
            frame_id=str(payload["frame_id"]),
            source_uri=str(payload["source_uri"]),
            captured_at=str(payload["captured_at"]),
            measurements=dict(payload["measurements"]),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "source_uri": self.source_uri,
            "captured_at": self.captured_at,
            "measurements": dict(self.measurements),
        }


@dataclass(frozen=True)
class ReplayManifest:
    schema_version: int
    replay_id: str
    product_code: str
    size_group: str
    no_camera: bool
    frames: tuple[ReplayFrame, ...]
    source_ref: str = ""

    def __post_init__(self) -> None:
        for field_name in ("replay_id", "product_code", "size_group"):
            if not str(getattr(self, field_name)).strip():
                raise ValidationError(f"{field_name} is required")
        if not self.no_camera:
            raise ValidationError("no_camera replay manifest must set no_camera=true")
        if not self.frames:
            raise ValidationError("frames is required")

    @classmethod
    def from_payload(cls, payload: Any) -> "ReplayManifest":
        if not isinstance(payload, dict):
            raise ValidationError("replay manifest must be an object")
        for field_name in ("schema_version", "replay_id", "product_code", "size_group", "no_camera", "frames"):
            if field_name not in payload:
                raise ValidationError(f"{field_name} is required")
        frames = payload["frames"]
        if not isinstance(frames, list) or not frames:
            raise ValidationError("frames is required")
        return cls(
            schema_version=int(payload["schema_version"]),
            replay_id=str(payload["replay_id"]),
            product_code=str(payload["product_code"]),
            size_group=str(payload["size_group"]),
            no_camera=bool(payload["no_camera"]),
            frames=tuple(ReplayFrame.from_payload(frame) for frame in frames),
            source_ref=str(payload.get("source_ref", "")),
        )

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "replay_id": self.replay_id,
            "product_code": self.product_code,
            "size_group": self.size_group,
            "no_camera": self.no_camera,
            "frames": [frame.to_payload() for frame in self.frames],
        }
        if self.source_ref:
            payload["source_ref"] = self.source_ref
        return payload


@dataclass(frozen=True)
class ReplayRunResult:
    replay_id: str
    mode: str
    product_code: str
    size_group: str
    frame_count: int
    decision: DecisionResult
    frames: tuple[ReplayFrame, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "replay_id": self.replay_id,
            "mode": self.mode,
            "product_code": self.product_code,
            "size_group": self.size_group,
            "frame_count": self.frame_count,
            "decision": self.decision.to_payload(),
            "frames": [frame.to_payload() for frame in self.frames],
        }


def load_replay_manifest(path: str | Path) -> ReplayManifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ReplayManifest.from_payload(data)


def run_no_camera_replay(
    *,
    manifest_path: str | Path,
    product_specs_path: str | Path,
    calibration_path: str | Path,
) -> ReplayRunResult:
    manifest = load_replay_manifest(manifest_path)
    product_spec = load_product_specs(product_specs_path).resolve(
        product_code=manifest.product_code,
        size_group=manifest.size_group,
    )
    calibration = load_calibration_config(calibration_path)
    geometry = resolve_geometry_measurements(manifest.frames[0].measurements)
    decision = evaluate_phase_two_geometry(
        product_spec=product_spec,
        calibration=calibration,
        geometry=geometry,
    )
    return ReplayRunResult(
        replay_id=manifest.replay_id,
        mode="no_camera_replay",
        product_code=manifest.product_code,
        size_group=manifest.size_group,
        frame_count=len(manifest.frames),
        decision=decision,
        frames=manifest.frames,
    )
