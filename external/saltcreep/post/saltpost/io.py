"""Read saltcreep result folders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import pandas as pd


@dataclass
class CaseResult:
    path: Path
    metadata: dict
    closure: pd.DataFrame | None = None
    displacements: pd.DataFrame | None = None
    displacement_profile: pd.DataFrame | None = None
    wall_profile: pd.DataFrame | None = None
    damage_wall: pd.DataFrame | None = None
    damage_events: pd.DataFrame | None = None

    @property
    def case_name(self) -> str:
        return str(self.metadata.get("case_name") or self.path.name)

    @property
    def element_type(self) -> str:
        return str(self.metadata.get("element_type") or "unknown")

    @property
    def n_dofs(self) -> int | None:
        value = self.metadata.get("n_dofs")
        return int(value) if value is not None else None

    @property
    def final_closure(self) -> float | None:
        if self.closure is None or self.closure.empty:
            return None
        return float(self.closure["closure_pct"].iloc[-1])

    @property
    def inner_radius_m(self) -> float | None:
        if self.displacement_profile is not None and not self.displacement_profile.empty:
            return float(self.displacement_profile["r_m"].min())
        if self.displacements is not None and not self.displacements.empty:
            if "r_m" in self.displacements:
                return float(self.displacements["r_m"].min())
        if self.closure is not None and not self.closure.empty and "u_wall_m" in self.closure:
            closure = float(self.closure["closure_pct"].iloc[-1])
            u_wall = float(self.closure["u_wall_m"].iloc[-1])
            if abs(closure) > 1.0e-30:
                return abs(u_wall) * 100.0 / abs(closure)
        return None


def load_metadata(result_dir: Path) -> dict:
    metadata_path = result_dir / "metadata.json"
    if not metadata_path.exists():
        return {"case_name": result_dir.name}
    with metadata_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_csv_if_exists(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


def load_result(result_dir: str | Path) -> CaseResult:
    path = Path(result_dir)
    metadata = load_metadata(path)
    closure = load_csv_if_exists(path / "closure.csv")
    displacements = load_csv_if_exists(path / "displacements.csv")
    displacement_profile = load_csv_if_exists(path / "displacements_profile.csv")
    wall_profile = load_csv_if_exists(path / "wall_profile.csv")
    damage_wall = load_csv_if_exists(path / "damage_wall.csv")
    damage_events = load_csv_if_exists(path / "damage_events.csv")
    return CaseResult(path=path, metadata=metadata, closure=closure,
                      displacements=displacements,
                      displacement_profile=displacement_profile,
                      wall_profile=wall_profile,
                      damage_wall=damage_wall,
                      damage_events=damage_events)
