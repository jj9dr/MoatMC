import numpy as np

def simulate_gross_margin_paths(margins, state, years=5, sims=2000):
    margins = np.array(margins, dtype=float)

    if len(margins) < 5:
        return {"ok": False, "reason": "Not enough margin history"}

    mu = np.mean(margins)
    sigma = np.std(margins)

    drift = 0.0
    if state == "Strong":
        drift = 0.002
    elif state == "Pre-Moat":
        drift = -0.002

    paths = np.zeros((sims, years))
    paths[:, 0] = mu

    for t in range(1, years):
        shocks = np.random.normal(drift, sigma, sims)
        paths[:, t] = np.clip(paths[:, t-1] + shocks, 0.02, 0.95)

    final = paths[:, -1]

    return {
        "ok": True,
        "years": years,
        "p_stay_in_band": float(np.mean(final > mu - 0.05)),
        "p_deteriorate_5pts": float(np.mean(final < mu - 0.05)),
        "p10": float(np.percentile(final, 10)),
        "p50": float(np.percentile(final, 50)),
        "p90": float(np.percentile(final, 90)),
    }
