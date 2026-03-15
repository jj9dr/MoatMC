from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import math
import random


# -----------------------------
# Utilities
# -----------------------------

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _clean_gm_series(margins: List[float]) -> List[float]:
    """
    Accepts gross margins as decimals (0.70) already.
    Removes None/NaN and clamps to [0, 1].
    """
    vals: List[float] = []
    for m in margins or []:
        if m is None:
            continue
        try:
            x = float(m)
        except Exception:
            continue
        if math.isnan(x):
            continue
        vals.append(_clamp(x, 0.0, 1.0))
    return vals


# -----------------------------
# Core metrics
# -----------------------------

def compute_gm_volatility_pp(margins: List[float]) -> float:
    """
    Volatility of gross margin history measured as stdev in percentage points.
    Example: margins [0.70, 0.72, 0.74] => stdev ~0.02 => 2.0pp
    """
    vals = _clean_gm_series(margins)
    if len(vals) < 2:
        return 0.0

    mean = sum(vals) / len(vals)
    var = sum((x - mean) ** 2 for x in vals) / (len(vals) - 1)
    sd = math.sqrt(var)  # decimal
    return sd * 100.0    # percentage points


def classify_moat_state(gm_vol_pp: float) -> str:
    """
    Simple classifier: lower GM volatility => stronger moat (more stable economics).
    You can tune these thresholds later.
    """
    if gm_vol_pp <= 1.5:
        return "Strong"
    if gm_vol_pp <= 3.0:
        return "Moderate"
    return "Weak"


def assess_model_confidence(margins: List[float]) -> Dict[str, object]:
    """
    Confidence score based on how many usable margin data points we have.
    Returns dict: {ok, score, label, reason}
    """
    vals = _clean_gm_series(margins)
    n = len(vals)

    if n >= 8:
        return {"ok": True, "score": 0.85, "label": "High", "reason": f"{n} usable points"}
    if n >= 5:
        return {"ok": True, "score": 0.60, "label": "Medium", "reason": f"{n} usable points"}
    if n >= 3:
        return {"ok": True, "score": 0.35, "label": "Low", "reason": f"Only {n} usable points"}
    return {"ok": False, "score": 0.10, "label": "Low", "reason": "Insufficient gross margin history"}


# -----------------------------
# Monte Carlo
# -----------------------------

def simulate_gross_margin_paths(
    start_margin: float,
    volatility: float,
    years: int,
    sims: int,
    floor: float = 0.0,
    cap: float = 0.85,
    band_width_pp: float = 2.5,
) -> Dict[str, object]:
    """
    Simple random walk simulation (Gaussian steps).
    volatility is a decimal stdev PER YEAR (e.g. 0.017 for 1.7pp).

    band_width_pp is the "stable band" width around start margin, in percentage points.
    Default 2.5pp = 0.025 decimal.
    """
    start = _clamp(float(start_margin), 0.0, 1.0)
    vol = max(0.0, float(volatility))
    years = int(years)
    sims = int(sims)

    if years < 1:
        years = 1
    if sims < 100:
        sims = 100

    band_width_pp : float = 5.0
    lo_band = start - band
    hi_band = start + band

    finals: List[float] = []
    stay_count = 0
    drop5_count = 0

    for _ in range(sims):
        m = start
        stayed = True

        for _t in range(years):
            # one-year shock
            shock = random.gauss(0.0, vol)
            m = _clamp(m + shock, floor, cap)

            if not (lo_band <= m <= hi_band):
                stayed = False

        finals.append(m)

        if stayed:
            stay_count += 1

        # "≥5pt deterioration" = final margin <= start - 0.05
        if m <= start - 0.05:
            drop5_count += 1

    finals_sorted = sorted(finals)

    def _pct(p: float) -> float:
        if not finals_sorted:
            return start
        idx = int(round((len(finals_sorted) - 1) * p))
        return finals_sorted[_clamp(idx, 0, len(finals_sorted) - 1)]

    p10 = _pct(0.10)
    p50 = _pct(0.50)
    p90 = _pct(0.90)

    return {
        "years": years,
        "sims": sims,
        "p_stay_in_band": stay_count / sims,
        "p_deteriorate_5pts": drop5_count / sims,
        "p10": p10,
        "p50": p50,
        "p90": p90,
    }


# -----------------------------
# One-shot assessment (Manual)
# -----------------------------

def assess_company_manual(
    company: str,
    gm_series: List[float],
    years: int = 5,
    sims: int = 2000,
    cap: float = 0.85,
) -> Dict[str, object]:
    """
    Manual inputs version (private or public).
    gm_series: list of gross margins (decimals). Example [0.70, 0.72, 0.74]
    """
    name = (company or "").strip() or "Company"
    margins = _clean_gm_series(gm_series)

    if len(margins) < 3:
        return {
            "ok": False,
            "company": name,
            "reason": "Need at least 3 gross margin points (e.g., 70,72,74).",
        }

    gm_vol_pp = compute_gm_volatility_pp(margins)
    state = classify_moat_state(gm_vol_pp)

    start_margin = margins[-1]
    vol_decimal = (gm_vol_pp / 100.0)

    mc = simulate_gross_margin_paths(
        start_margin=start_margin,
        volatility=vol_decimal,
        years=int(years),
        sims=int(sims),
        floor=0.0,
        cap=float(cap),
    )

    conf = assess_model_confidence(margins)

    return {
        "ok": True,
        "company": name,
        "moat_state": state,
        "gm_vol_pp": gm_vol_pp,
        "monte_carlo": mc,
        "confidence": conf,
    } 


   