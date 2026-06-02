# ADR-0002: SOP-First Deterministic Rule Engine

## Status

Draft for QC/domain owner review.

## Context

The app must not let model availability or detector confidence replace explicit
SOP logic. Geometry and product-spec rules have deterministic safety behavior.

## Decision

The SOP rule engine owns final inspection decisions. Product specs, calibration,
geometry measurements, detector observations, and image quality become inputs to
phase rules with reason codes.

## Alternatives Considered

- Detector decides PASS/NG directly: rejected because it collapses model output
  and SOP authority.
- Single global tolerance: rejected because the brief says SOP includes
  product-specific tolerance groups.

## Consequences

The app can safely block unknown products and missing calibration. Model-dependent
rules can remain `NOT_EVALUATED`, `ASSIST`, or `BLOCKED` until model approval.

## Security And Data Impact

Rule decisions must be audit logged with source config versions.

## Rollback Or Migration Impact

Rule config changes require compatibility notes, tests, and rollback to prior
config version.
