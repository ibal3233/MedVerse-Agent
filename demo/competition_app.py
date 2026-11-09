from __future__ import annotations

from pathlib import Path
import sys
import json

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from medverse.integration.gate19_grounded_pipeline import Gate19GroundedPipeline
from demo.judge_view_model import build_judge_view, humanize_code


st.set_page_config(
    page_title="MedVerse-Agent | Trustworthy Medical Metaverse Coordination",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
:root {
  --bg:#07101c; --panel:#0d1928; --panel2:#101f31; --line:#263b55;
  --text:#edf4fb; --muted:#97abc1; --accent:#58c8e8; --good:#57d6a1;
  --warn:#f1c66b; --bad:#ef7d8a;
}
.stApp {background:linear-gradient(180deg,#0a1524 0%,#07101c 100%);color:var(--text);}
.block-container {max-width:1540px;padding-top:1.1rem;padding-bottom:2.5rem;}
.hero {padding:20px 22px;border:1px solid var(--line);border-radius:18px;
       background:linear-gradient(110deg,#10263b,#0b1725);margin-bottom:14px;}
.hero h1 {margin:0;font-size:31px;}
.hero p {margin:7px 0 0;color:var(--muted);font-size:14px;}
.panel {border:1px solid var(--line);border-radius:15px;background:var(--panel);
        padding:14px 15px;margin-bottom:12px;}
.title {font-size:11px;letter-spacing:.10em;text-transform:uppercase;
        color:#aac0d8;font-weight:800;margin-bottom:9px;}
.big {font-size:25px;font-weight:850;line-height:1.15;}
.small {font-size:11px;color:var(--muted);}
.badge {display:inline-block;padding:5px 9px;border-radius:999px;border:1px solid #35516d;
        background:#0b1d2f;margin:3px 4px 3px 0;font-size:11px;font-weight:700;}
.good {color:#77e1b6;border-color:#287a5d;}
.warn {color:#f5d486;border-color:#81682b;}
.bad {color:#f4a0aa;border-color:#82414a;}
.agent {border:1px solid #2a4059;border-radius:13px;background:#0a1725;padding:12px;margin-bottom:10px;}
.agent h4 {margin:0 0 2px;font-size:15px;}
.agent-role {font-size:11px;color:var(--muted);margin-bottom:8px;}
.code {font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10px;color:#94b7d5;}
.policy {border-left:3px solid #4b7896;background:#0b1724;padding:9px 11px;margin:7px 0;border-radius:0 10px 10px 0;}
.policy b {font-size:12px;}
.policy .meta {font-size:10px;color:var(--muted);margin-top:3px;}
.action {padding:7px 9px;border:1px solid #29445f;border-radius:9px;background:#0a1827;margin:5px 0;font-size:11px;}
.footer {text-align:center;color:#70879e;font-size:10px;margin-top:18px;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

CASE_FILE = ROOT / "data" / "evaluation" / "gate19_end_to_end_cases.json"
CASE_DATA = json.loads(CASE_FILE.read_text(encoding="utf-8"))
CASES = {c["scenario_id"]: c for c in CASE_DATA["cases"]}

SCENARIO_LABELS = {
    "S1": "S1 — Digital Twin Cannot Be Trusted",
    "S2": "S2 — Care vs Research Consent",
    "S3": "S3 — Unverified DT + High-Impact AI",
    "S4": "S4 — Unauthorized Disclosure",
}


@st.cache_resource(show_spinner="Loading Korean policy embeddings…")
def get_pipeline():
    return Gate19GroundedPipeline(ROOT)


@st.cache_data(show_spinner=False)
def run_scenario_cached(scenario_id: str):
    # Pipeline object is separately cached; this function is intentionally simple.
    # Streamlit does not serialize the model itself.
    pipeline = get_pipeline()
    return pipeline.run_case(CASES[scenario_id])


def status_badge(text, kind=""):
    return f'<span class="badge {kind}">{text}</span>'


def boundary_kind(status: str):
    if status == "COMPLIANT":
        return "good"
    if status in {"OUT_OF_POLICY", "WRONG_JURISDICTION", "OUTSIDE_MANDATE"}:
        return "bad"
    return "warn"


st.markdown(
    """
    <div class="hero">
      <h1>MedVerse-Agent</h1>
      <p>
        Policy-grounded multi-agent institutional coordination for trustworthy
        Medical Metaverse systems. Institutional agents advise within bounded mandates;
        MedVerse-Agent harmonizes actions under Korean policy constraints.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

top1, top2, top3, top4 = st.columns([2.1, 1, 1, 1])
with top1:
    selected_label = st.selectbox(
        "Validated scenario",
        [SCENARIO_LABELS[k] for k in ["S1", "S2", "S3", "S4"]],
        label_visibility="collapsed",
    )
    sid = selected_label.split(" — ")[0]

with top2:
    st.markdown(
        '<div class="panel"><div class="title">Jurisdiction</div>'
        '<div class="big">Republic of Korea</div><div class="small">KR hard-filtered before semantic ranking</div></div>',
        unsafe_allow_html=True,
    )
with top3:
    st.markdown(
        '<div class="panel"><div class="title">Institutional agents</div>'
        '<div class="big">5</div><div class="small">bounded mandates across S1–S4</div></div>',
        unsafe_allow_html=True,
    )
with top4:
    st.markdown(
        '<div class="panel"><div class="title">End-to-end validation</div>'
        '<div class="big" style="color:#77e1b6;">35 / 35</div><div class="small">Gate 19 PASS</div></div>',
        unsafe_allow_html=True,
    )

try:
    raw_result = run_scenario_cached(sid)
except Exception as exc:
    st.error(f"Validated pipeline could not be executed in this runtime: {exc}")
    st.stop()

case = CASES[sid]
view = build_judge_view(raw_result["judge_trace"], case["name"])

# ------------------------------------------------------------------
# Layer 1: Digital Twin
# ------------------------------------------------------------------
dt_col, out_col = st.columns([1.05, 1.95])
with dt_col:
    validity = view["digital_twin"]["validity"]
    vk = "good" if validity == "VALID" else ("warn" if validity == "DEGRADED" else "bad")
    st.markdown(
        f"""
        <div class="panel">
          <div class="title">1 · Patient Digital Twin</div>
          <div class="big">{view["digital_twin"]["validity_label"]}</div>
          <div style="margin-top:8px;">{status_badge(validity, vk)}</div>
          <div class="small" style="margin-top:10px;">
            Validity is derived from freshness, integrity, completeness,
            provenance, and uncertainty metadata. It is not a diagnosis.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with out_col:
    st.markdown(
        f"""
        <div class="panel">
          <div class="title">Scenario</div>
          <div class="big">{case["name"]}</div>
          <div class="small" style="margin-top:7px;">{case.get("description","")}</div>
          <div style="margin-top:11px;">
            {status_badge("Controlled event-driven simulation")}
            {status_badge("No autonomous care", "warn")}
            {status_badge("Population data ≠ patient inference", "good")}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------
# Layers 2–4: agents + policy + boundary
# ------------------------------------------------------------------
st.markdown("### Institutional assessments and Korean-policy boundaries")

agent_cols = st.columns(len(view["agents"]))
for col, agent in zip(agent_cols, view["agents"]):
    with col:
        bkind = boundary_kind(agent["policy_boundary_status"])
        policies_html = ""
        for hit in agent["retrieved_policy"][:3]:
            score = hit.get("score")
            score_text = f"{float(score):.3f}" if score is not None else "—"
            url = hit.get("official_url", "")
            link = (
                f'<a href="{url}" target="_blank" style="color:#7dd6ee;">official source</a>'
                if url else "source URL unavailable"
            )
            policies_html += f"""
            <div class="policy">
              <b>{hit["chunk_id"]}</b>
              <div class="meta">
                {hit["authority"]} · {hit["source_type"]}<br>
                {hit["locator"]} · similarity {score_text}<br>
                {link}
              </div>
            </div>
            """

        actions_html = "".join(
            f'<div class="action">{humanize_code(a)}</div>'
            for a in agent["recommended_actions"][:4]
        )
        st.markdown(
            f"""
            <div class="agent">
              <h4>{agent["name"]}</h4>
              <div class="agent-role">{agent["role"]}</div>
              <div>{status_badge(agent["risk"] or "ASSESSED", "warn" if agent["risk"]=="HIGH" else "")}</div>
              <div class="small" style="margin-top:8px;"><b>Assessment</b></div>
              <div>{agent["assessment_label"]}</div>
              <div class="code">{agent["assessment_code"]}</div>

              <div class="small" style="margin-top:10px;"><b>Agent recommendations</b></div>
              {actions_html}

              <div class="small" style="margin-top:10px;"><b>Selected policy-boundary action</b></div>
              <div class="action">{agent["selected_boundary_action_label"]}</div>

              <div class="small" style="margin-top:10px;"><b>Boundary result</b></div>
              <div>{status_badge(agent["policy_boundary_label"], bkind)} {status_badge(agent["enforcement"])}</div>

              <div class="small" style="margin-top:11px;"><b>Retrieved Korean policy</b></div>
              {policies_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------------
# Layer 5: MedVerse-Agent coordination
# ------------------------------------------------------------------
coord = view["coordination"]
st.markdown("### MedVerse-Agent harmonization")

c1, c2 = st.columns([1.25, 1.75])
with c1:
    state_kind = (
        "good" if coord["state"] in {"AGREEMENT", "COMPLEMENTARY"}
        else "warn" if coord["state"] in {"CONDITIONAL_HARMONIZATION", "INSTITUTIONAL_CONFLICT", "INSUFFICIENT_EVIDENCE"}
        else "bad"
    )
    st.markdown(
        f"""
        <div class="panel">
          <div class="title">Coordination state</div>
          <div class="big">{coord["state_label"]}</div>
          <div style="margin-top:9px;">{status_badge(coord["state"], state_kind)}</div>
          <div class="small" style="margin-top:10px;"><b>Rationale</b></div>
          <div>{coord["rationale_label"]}</div>
          <div class="code">{coord["rationale_code"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="panel">
          <div class="title">Final institutional outcome</div>
          <div class="big">{view["outcome"]["label"]}</div>
          <div class="code" style="margin-top:7px;">{view["outcome"]["code"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown('<div class="panel"><div class="title">Harmonized response</div>', unsafe_allow_html=True)

    if coord["accepted_actions"]:
        st.markdown("**Accepted actions**")
        for item in coord["accepted_actions"]:
            st.markdown(
                f"- **{humanize_code(item['agent_id'])}:** {humanize_code(item['action'])}"
            )

    if coord["blocked_actions"]:
        st.markdown("**Blocked actions**")
        for item in coord["blocked_actions"]:
            st.markdown(
                f"- **{humanize_code(item['agent_id'])}:** {humanize_code(item['action'])} — {humanize_code(item.get('reason',''))}"
            )

    if coord["conditional_steps"]:
        st.markdown("**Conditional workflow**")
        for step in coord["conditional_steps"]:
            cond = f" ({humanize_code(step['condition'])})" if step.get("condition") else ""
            st.markdown(
                f"- Step {step.get('step','—')}: **{humanize_code(step.get('owner',''))}** → "
                f"{humanize_code(step.get('action',''))}{cond}"
            )

    if coord["evidence_requests"]:
        st.markdown("**Additional evidence requested**")
        for req in coord["evidence_requests"]:
            st.markdown(
                f"- {humanize_code(req.get('requesting_agent',''))}: {humanize_code(req.get('evidence',''))}"
            )

    if coord["messages"]:
        st.markdown("**Minimum-necessary inter-agent messages**")
        for m in coord["messages"]:
            st.markdown(
                f"- **{humanize_code(m.get('from',''))} → {humanize_code(m.get('to',''))}:** "
                f"`{m.get('message','')}`"
            )

    if coord["escalation_required"]:
        st.markdown("**Human escalation**")
        for t in coord["escalation_targets"]:
            st.markdown(f"- {humanize_code(t)}")

    st.markdown("</div>", unsafe_allow_html=True)

# Evidence / audit panel
with st.expander("Audit trace and evidence-boundary checks"):
    for agent in view["agents"]:
        st.markdown(f"**{agent['name']}**")
        st.write({
            "policy_ids": agent["policy_ids"],
            "dt_evidence_used": agent["dt_evidence_used"],
            "open_data_evidence_used": agent["open_data_evidence_used"],
            "patient_level_inference_from_population_data":
                agent["patient_level_inference_from_population_data"],
            "unauthorized_evidence_used":
                agent["unauthorized_evidence_used"],
        })

st.markdown(
    """
    <div class="footer">
      Research sandbox / demonstrator. Controlled event-driven Medical Metaverse simulation.
      Not clinical validation, regulatory certification, legal advice, or autonomous patient care.
    </div>
    """,
    unsafe_allow_html=True,
)
