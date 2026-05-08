"""
HD Pro — Production Human Design Engine wrapping pyhd (Swiss Ephemeris backend).

Provides clean dict/JSON output, batch processing, and comparison tools.
"""

from datetime import UTC, datetime
from typing import Any

from pyhd import Chart as PyHDChart
from pyhd.constants import Planets


class HDEngine:
    """Production-grade Human Design calculator."""

    def __init__(self, birth_dt: datetime):
        if birth_dt.tzinfo is None:
            birth_dt = birth_dt.replace(tzinfo=UTC)
        self.birth_dt = birth_dt.astimezone(UTC)
        self._chart = PyHDChart(self.birth_dt)

    @property
    def chart(self) -> PyHDChart:
        return self._chart

    def to_dict(self) -> dict[str, Any]:
        """Full chart as clean JSON-serializable dict."""
        c = self._chart
        return {
            "birth": {
                "datetime": self.birth_dt.isoformat(),
                "design_datetime": c.design.dt.isoformat(),
            },
            "type": str(c.type),
            "type_name": c.type.title if hasattr(c.type, 'title') else str(c.type),
            "authority": str(c.authority),
            "profile": str(c.profile),
            "profile_name": str(c.profile.title) if hasattr(c.profile, 'title') else str(c.profile),
            "incarnation_cross": str(c.cross),
            "cross_full": str(c.cross.full_name) if hasattr(c.cross, 'full_name') else str(c.cross),
            "definition": str(c.definition_type),
            "strategy": str(c.strategy),
            "signature": str(c.signature),
            "not_self_theme": str(c.not_self_theme),
            "geometry": str(c.geometry) if hasattr(c, 'geometry') else None,
            "destiny": str(c.destiny) if hasattr(c, 'destiny') else None,
            "defined_centers": [str(ctr) for ctr in c.centers],
            "defined_channels": [
                {"name": ch.name, "gates": list(ch.num), "full_name": str(ch.full_name) if hasattr(ch, 'full_name') else str(ch)}
                for ch in c.channels
            ],
            "activated_gates": sorted([g.num for g in c.gates]),
            "definitions": [
                [str(ctr) for ctr in group]
                for group in c.definitions
            ],
            # Variables
            "variables": {
                "determination": str(c.determination) if hasattr(c, 'determination') else None,
                "cognition": str(c.cognition) if hasattr(c, 'cognition') else None,
                "environment": str(c.environment) if hasattr(c, 'environment') else None,
                "perspective": str(c.perspective) if hasattr(c, 'perspective') else None,
                "motivation": str(c.motivation) if hasattr(c, 'motivation') else None,
                "sense": str(c.sense) if hasattr(c, 'sense') else None,
                "orientations": str(c.variable_orientations) if hasattr(c, 'variable_orientations') else None,
            },
            # Detailed activations
            "activations": self._activations_dict(),
            # Gate statistics
            "gate_count": c.num_gates,
            "channel_count": c.num_channels,
            "center_count": c.num_centers,
            "definition_count": c.num_definitions,
        }

    def _activations_dict(self) -> list[dict]:
        """All 26 activations as a list of dicts."""
        results = []
        for label, imprint in [("Design", self._chart.design), ("Personality", self._chart.personality)]:
            for planet in Planets:
                a = imprint.activations[planet]
                results.append({
                    "imprint": label,
                    "planet": str(planet),
                    "planet_symbol": planet.symbol,
                    "gate": a.gate.num,
                    "gate_name": str(a.gate.title) if hasattr(a.gate, 'title') else str(a.gate),
                    "line": a.line.num if a.line else None,
                    "color": a.color.num if a.color else None,
                    "tone": a.tone.num if a.tone else None,
                    "base": a.base.num if a.base else None,
                    "longitude": round(a.longitude, 6),
                })
        return results

    def summary_text(self) -> str:
        """Human-readable summary."""
        d = self.to_dict()
        chs = ", ".join(f"{g1}-{g2} {n}" for n, (g1, g2) in 
              [(ch["name"], tuple(ch["gates"])) for ch in d["defined_channels"]]) or "none"
        cross_name = d["cross_full"].split("(")[0].strip() if "(" in d["cross_full"] else d["cross_full"]
        return (
            f"Type: {d['type']} | Authority: {d['authority']} | Profile: {d['profile']}\n"
            f"Cross: {cross_name}\n"
            f"Definition: {d['definition']} | Strategy: {d['strategy']}\n"
            f"Defined Centers ({d['center_count']}): {', '.join(d['defined_centers'])}\n"
            f"Channels ({d['channel_count']}): {chs}\n"
            f"Gates ({d['gate_count']}): {d['activated_gates']}"
        )
