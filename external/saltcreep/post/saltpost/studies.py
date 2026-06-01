"""Declarative study discovery for saltpost."""

from __future__ import annotations

from pathlib import Path
import re

from .io import CaseResult
from .registry import discover_results


VALID_VARY = {"element", "constitutive", "thermal"}


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _case_tokens(result: CaseResult) -> str:
    values = [
        result.case_name,
        result.path.name,
        str(result.metadata.get("study") or ""),
        str(result.metadata.get("physical_case") or ""),
    ]
    return " ".join(_normalize(v) for v in values)


def result_matches_study(result: CaseResult, study: str) -> bool:
    """Return true when a result belongs to a named physical study."""
    target = _normalize(study)
    if not target:
        return True
    tokens = _case_tokens(result)
    return target in tokens.split("_") or target in tokens


def constitutive_variant(result: CaseResult) -> str:
    """Infer a concise constitutive variant from metadata and case naming."""
    metadata = result.metadata
    flags = metadata.get("creep_flags") or {}
    name = _normalize(result.case_name)

    explicit = (
        metadata.get("constitutive_model")
        or metadata.get("creep_model")
        or metadata.get("tertiary_model")
        or metadata.get("primary_model")
    )
    if explicit:
        return str(explicit)

    if "aubertin" in name or "isv_sh_d" in name:
        return "aubertin_isv_sh_d"
    if "wang" in name:
        return "wang_2004"
    if "motta" in name or "damage" in name or flags.get("tertiary"):
        return "MottaV1"
    if "isv_sh_dm" in name:
        return "isv_sh_dm"
    if "edmt" in name or flags.get("primary"):
        return "EDMT"
    if flags.get("secondary"):
        return "DM"
    if metadata.get("elastic_only"):
        return "elastic"
    return "unknown"


def thermal_variant(result: CaseResult) -> str:
    """Infer thermal mode from metadata and conventional result names."""
    metadata = result.metadata
    name = _normalize(result.case_name)
    explicit = metadata.get("thermal_mode") or metadata.get("temperature_field")
    if explicit:
        return str(explicit)
    if not metadata.get("thermal_enabled", False):
        return "none"
    if "conduction_2d" in name or "thermal_2d" in name:
        return "conduction_2d"
    if "conduction_1d" in name or "thermal_1d" in name:
        return "conduction_1d"
    if "profile" in name:
        return "profile"
    return "thermal"


def variant_key(result: CaseResult, vary: str) -> str:
    if vary == "element":
        return result.element_type
    if vary == "constitutive":
        return constitutive_variant(result)
    if vary == "thermal":
        return thermal_variant(result)
    raise ValueError(f"unknown study variation: {vary}")


def discover_study_results(
    study: str,
    vary: str,
    results_root: str | Path = "results",
) -> list[CaseResult]:
    """Discover result folders for a named study and variation axis."""
    if vary not in VALID_VARY:
        raise ValueError(f"vary must be one of {sorted(VALID_VARY)}")

    root = Path(results_root)
    results = discover_results(str(root / "*"))
    selected = [r for r in results if result_matches_study(r, study)]
    selected.sort(key=lambda r: (variant_key(r, vary), r.case_name))
    return selected

