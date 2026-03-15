from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


STRUCTURAL_MOAT_VALUES = ("WEAK", "PRE_MOAT", "STRONG")
DURABILITY_REGIME_VALUES = ("STABLE", "AT_RISK", "DECAYING")
DATA_CONFIDENCE_VALUES = ("HIGH", "MEDIUM", "LOW")


def normalize_structural_moat(state: str) -> str:
    """
    Maps your internal moat labels to canonical M+M_C v1.0 output.
    """
    s = (state or "").strip().lower()
    if "strong" in s:
        return "STRONG"
    if "pre" in s:
        return "PRE_MOAT"
    return "WEAK"


def derive_durability_regime(prob_break: float) -> str:
    """
    Canonical rules:
      <= 30% -> STABLE
      30-70% -> AT_RISK
      >= 70% -> DECAYING
    """
    if prob_break <= 0.30:
        return "STABLE"
    if prob_break <= 0.70:
        return "AT_RISK"
    return "DECAYING"


def derive_data_confidence(n_years: int, has_missing: bool) -> str:
    """
    Simple, defensible rule:
      HIGH   = >=5 years and no missing values
      MEDIUM = 3-4 years OR has missing values
      LOW    = <3 years
    """
    if n_years < 3:
        return "LOW"
    if n_years >= 5 and not has_missing:
        return "HIGH"
    return "MEDIUM"


def cap_probability(p: float) -> float:
    """
    Presentation cap: never show fake certainty.
    """
    return min(0.95, max(0.05, float(p)))


@dataclass
class MMCResult:
    ticker: str
    as_of: str

    MMC_STRUCTURAL_MOAT: str
    MMC_MARGIN_VOLATILITY: Optional[float]

    MMC_DURABILITY_PROB_BREAK: float
    MMC_DURABILITY_REGIME: str

    MMC_DATA_CONFIDENCE: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "as_of": self.as_of,
            "MMC_STRUCTURAL_MOAT": self.MMC_STRUCTURAL_MOAT,
            "MMC_MARGIN_VOLATILITY": self.MMC_MARGIN_VOLATILITY,
            "MMC_DURABILITY_PROB_BREAK": self.MMC_DURABILITY_PROB_BREAK,
            "MMC_DURABILITY_REGIME": self.MMC_DURABILITY_REGIME,
            "MMC_DATA_CONFIDENCE": self.MMC_DATA_CONFIDENCE,
        }


def now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")