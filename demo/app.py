from __future__ import annotations

from pathlib import Path
import sys
import json

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from medverse.integration.pipeline import MedVerseIntegratedPipeline

st.set_page_config(
    page_title="MedVerse-Agent",
    layout="wide",
)

st.title("MedVerse-Agent")
st.caption(
    "Policy-Grounded Multi-Agent Institutional Coordination "
    "for Trustworthy Medical Metaverse Systems"
)

if "pipeline" not in st.session_state:
    st.session_state.pipeline = MedVerseIntegratedPipeline(ROOT)

pipeline = st.session_state.pipeline

c1, c2 = st.columns([1, 1])

with c1:
    if st.button(
        "Release next event",
        disabled=pipeline.done,
        use_container_width=True,
    ):
        st.session_state.last_entry = pipeline.release_next_event()

with c2:
    if st.button("Reset scenario", use_container_width=True):
        pipeline.reset()
        st.session_state.last_entry = None
        st.rerun()

st.divider()

left, center, right = st.columns([1.1, 1.1, 1.3])

with left:
    st.subheader("Medical Metaverse State")

    state = pipeline.env.state.to_dict()

    st.metric(
        "SpO₂",
        f"{state['clinical']['spo2']:.0f}%",
    )
    st.metric(
        "Heart rate",
        f"{state['clinical']['heart_rate']:.0f} bpm",
    )
    st.metric(
        "Packet loss",
        f"{100*state['network']['packet_loss']:.0f}%",
    )
    st.metric(
        "RTT",
        f"{state['network']['rtt_ms']:.0f} ms",
    )
    st.metric(
        "DT validity",
        state["dt"]["validity"],
    )

with center:
    st.subheader("Institutional Agents")

    hospital = pipeline.assessments.get("E1")
    if hospital:
        st.markdown("**Healthcare Provider Agent**")
        st.write(hospital.assessment_code)
        st.write(f"Risk: {hospital.risk}")
        st.write("Observed:", ", ".join(hospital.observed_fields))
    else:
        st.info("Hospital Agent has not received an authorized event yet.")

    st.divider()

    cyber = pipeline.assessments.get("E3") or pipeline.assessments.get("E2")
    if cyber:
        st.markdown("**Cyber / Network Agent**")
        st.write(cyber.assessment_code)
        st.write(f"Risk: {cyber.risk}")
        st.write("Observed:", ", ".join(cyber.observed_fields))
    else:
        st.info("Cyber/Network Agent has not received an authorized event yet.")

with right:
    st.subheader("Coordination")

    if pipeline.last_coordination:
        d = pipeline.last_coordination
        st.success(d["coordination_state"])
        st.write(d["rationale_code"])
        st.write(
            "Human review:",
            "REQUIRED" if d["human_review_required"] else "Not required",
        )

        with st.expander("Joint actions", expanded=True):
            for action in d["joint_actions"]:
                st.write("•", action)

        if pipeline.last_explanation:
            with st.expander("Policy-grounded explanation", expanded=True):
                st.write(pipeline.last_explanation["summary"])
                st.write(
                    "Policy chunks:",
                    ", ".join(
                        pipeline.last_explanation["cited_policy_chunks"]
                    ),
                )
    else:
        st.info(
            "Coordination begins when complementary institutional "
            "assessments become available."
        )

st.divider()

st.subheader("Progressive Scenario Timeline")

if not pipeline.audit_log:
    st.info("No event released yet.")

for entry in pipeline.audit_log:
    with st.expander(
        f"{entry['event_id']} — {entry['event_type']}",
        expanded=True,
    ):
        st.write("Visible to:", ", ".join(entry["visible_to"]))
        st.json(entry["assessments"])

st.subheader("Audit / Provenance")

st.json(pipeline.audit_log)
