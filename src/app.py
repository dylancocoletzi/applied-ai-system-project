"""
Streamlit UI for the VibeFit Agent — the extended system's primary entry
point. Run with:

    streamlit run src/app.py

This is new code layered on top of the original, unmodified base project
(src/main.py + src/recommender.py). See README.md and
diagrams/architecture.mmd for the full pipeline.
"""
import streamlit as st

from agent import read_recent_activity, run_agent

EXAMPLE_PROMPTS = [
    "something upbeat pop for a workout",
    "sad acoustic songs for a rainy day",
    "aggressive metal but keep it chill and acoustic",
]

STATUS_BADGE = {
    "matched": "✅ matched",
    "defaulted": "➖ defaulted (no signal found)",
    "ambiguous": "⚠️ ambiguous (conflicting signals)",
}


def render_interpretation(confidence: dict) -> None:
    st.markdown("**How I interpreted your request**")
    rows = []
    for field, info in confidence.items():
        value = info["value"]
        if isinstance(value, list):
            value = " / ".join(value)
        rows.append(
            {
                "field": field,
                "resolved value": value if value else "(none)",
                "status": STATUS_BADGE.get(info["status"], info["status"]),
                "matched phrases": ", ".join(info["matched_phrases"]) or "—",
            }
        )
    st.table(rows)


def render_results(recommendations) -> None:
    if not recommendations:
        st.write("No recommendations found.")
        return
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        st.markdown(f"**{rank}. {song['title']} — {song['artist']}**  (score: {score:.2f})")
        for reason in explanation.split(" + "):
            st.markdown(f"- {reason}")


def render_recent_activity() -> None:
    events = read_recent_activity(limit=8)
    if not events:
        st.caption("No activity logged yet — submit a request to see it here.")
        return
    for event in reversed(events):
        top = event.get("top_result")
        top_desc = f"{top['title']} ({top['score']:.2f})" if top else "no results"
        st.caption(f"**{event['input_text']!r}** → {top_desc}")


def main() -> None:
    st.set_page_config(page_title="VibeFit Agent", page_icon="🎵")
    st.title("🎵 VibeFit Agent")
    st.write(
        "Describe the vibe you're after in your own words. The agent parses it, "
        "validates it, scores the catalog, and double-checks its own interpretation "
        "before showing you results."
    )

    with st.expander("How this works"):
        st.markdown(
            "1. **Plan** — free text is parsed into a structured profile "
            "(genre, mood, energy, acoustic preference) via keyword matching, "
            "with a confidence status per field.\n"
            "2. **Guardrail** — the profile is type-checked, case-normalized, "
            "and clamped to valid ranges.\n"
            "3. **Act** — the unmodified base-project scorer "
            "(`src/recommender.py`) ranks the catalog.\n"
            "4. **Check** — the agent flags low confidence or "
            "catalog-implausible combinations, without changing the result.\n\n"
            "See `diagrams/architecture.mmd` for the full diagram, and "
            "`src/main.py` for the original, unmodified base project this "
            "extends."
        )

    st.markdown("**Try an example:**")
    example_cols = st.columns(len(EXAMPLE_PROMPTS))
    for col, prompt in zip(example_cols, EXAMPLE_PROMPTS):
        if col.button(prompt):
            st.session_state["vibe_text"] = prompt

    text = st.text_area(
        "Describe the vibe you want",
        key="vibe_text",
        placeholder="e.g. something upbeat for a workout",
    )

    if st.button("Get recommendations", type="primary") and text.strip():
        result = run_agent(text, k=5)

        render_interpretation(result["confidence"])

        if result["guardrail_corrections"]:
            st.info("**Guardrail notes:**\n" + "\n".join(f"- {c}" for c in result["guardrail_corrections"]))

        if result["critique_flags"]:
            st.warning("**Self-check notes:**\n" + "\n".join(f"- {w}" for w in result["critique_flags"]))

        st.markdown("### Recommendations")
        render_results(result["recommendations"])

    with st.sidebar:
        st.markdown("### Recent Activity")
        render_recent_activity()
        st.markdown("---")
        st.caption(
            "Base project: `src/main.py` + `src/recommender.py` "
            "(unmodified, structured-profile CLI demo)."
        )


if __name__ == "__main__":
    main()
