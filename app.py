from __future__ import annotations

import streamlit as st
from moat_logic import assess_company_manual


# -----------------------------
# Page config + Styling
# -----------------------------
st.set_page_config(page_title="MoatMC", layout="centered")

st.markdown(
    """
    <style>
      /* Overall */
      .block-container { max-width: 860px; padding-top: 24px; }
      h1, h2, h3 { letter-spacing: 0.2px; }
      .muted { color: rgba(0,0,0,0.55); font-size: 0.95rem; }
      .tiny  { color: rgba(0,0,0,0.55); font-size: 0.85rem; }

      /* Panels */
      .panel {
        background: #f3f4f6;
        border: 1px solid rgba(0,0,0,0.06);
        border-radius: 14px;
        padding: 16px 16px 12px 16px;
        margin: 10px 0 14px 0;
      }

      .panel-title {
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 6px;
      }

      /* Summary "terminal" box */
      .terminal {
        background: #ffffff;
        border: 1px solid rgba(0,0,0,0.10);
        border-radius: 12px;
        padding: 12px 12px 10px 12px;
      }

      /* Make Streamlit metric a little tighter */
      div[data-testid="stMetric"] { padding: 6px 0px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("MoatMC")
st.caption("Standalone mode: manual inputs (private or public). Business quality signal, not a price call.")


# -----------------------------
# Inputs panel
# -----------------------------
st.markdown('<div class="panel"><div class="panel-title">Inputs</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns([2, 1, 1], gap="small")
with c1:
    company = st.text_input("Company / Ticker", value="Databricks")
with c2:
    years = st.selectbox("Horizon (years)", [3, 5, 10], index=1)
with c3:
    sims = st.selectbox("Simulations", [500, 2000, 10000], index=1)

st.markdown("**Gross margin history (manual)**")
st.markdown('<div class="tiny">Enter as percentages (e.g., 72.5) or decimals (e.g., 0.725). Minimum 3 points.</div>', unsafe_allow_html=True)

gm_text = st.text_area(
    "Gross margins (comma separated)",
    value="70, 72, 74, 75, 76",
    height=80,
)

run = st.button("Run")

st.markdown("</div>", unsafe_allow_html=True)  # close Inputs panel


def _parse_gm_series(text: str):
    parts = [p.strip() for p in (text or "").replace("\n", ",").split(",") if p.strip()]
    vals = []
    for p in parts:
        try:
            x = float(p)
            # If user typed percentages like 70, convert to 0.70
            if x > 1.5:
                x = x / 100.0
            vals.append(x)
        except Exception:
            pass
    return vals


# -----------------------------
# Run + Results
# -----------------------------
if run:
    gm_series = _parse_gm_series(gm_text)

    with st.spinner("Running MoatMC..."):
        result = assess_company_manual(company, gm_series, years=years, sims=sims)

    if not result.get("ok", False):
        st.error(result.get("reason", "Analysis failed"))
        st.stop()

    state = result["moat_state"]
    vol_pp = result["gm_vol_pp"]
    conf = result.get("confidence")
    mc = result["monte_carlo"]

    stay = mc["p_stay_in_band"]
    drop = mc["p_deteriorate_5pts"]

    # Results panel
    st.markdown('<div class="panel"><div class="panel-title">RESULT — {}</div>'.format(result["company"]), unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3, gap="small")
    m1.metric("Moat State", state)
    m2.metric("GM Volatility", f"{vol_pp:.2f}%")
    if conf and conf.get("ok"):
        m3.metric("Confidence", f"{conf['label']} ({conf['score']:.0%})")
    else:
        m3.metric("Confidence", "Low")

    st.markdown('<div class="muted">Interpretation: lower GM volatility generally implies more stable economics (stronger “moat”).</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close RESULT panel

    # Stability panel
    st.markdown('<div class="panel"><div class="panel-title">Stability (Monte Carlo)</div>', unsafe_allow_html=True)

    s1, s2 = st.columns(2, gap="small")
    s1.metric("Stay-stable probability", f"{stay:.0%}")
    s2.metric("≥5pt deterioration risk", f"{drop:.0%}")

    st.write(
        f"Year {mc['years']} GM (p10 / p50 / p90): "
        f"**{mc['p10']:.0%} / {mc['p50']:.0%} / {mc['p90']:.0%}**"
    )

    st.markdown("</div>", unsafe_allow_html=True)  # close Stability panel

    # Summary panel
    conf_txt = ""
    if conf and conf.get("ok"):
        conf_txt = f" | Conf {conf['label']} {conf['score']:.0%}"

    x_text = (
        f"MoatMC: {result['company']} | {state} | GM vol {vol_pp:.2f}%\n"
        f"MC {mc['years']}y stay-stable {stay:.0%}, ≥5pt drop {drop:.0%}"
        f"{conf_txt}\n"
        f"(Business quality signal, not a price call)"
    )

    st.markdown('<div class="panel"><div class="panel-title">Summary</div>', unsafe_allow_html=True)
    st.markdown('<div class="terminal">', unsafe_allow_html=True)
    st.text_area("Copy/paste", x_text, height=95)
    st.markdown("</div></div>", unsafe_allow_html=True)  # close terminal + panel
