"""GenPal Question Bank Factory — Streamlit prototype entry point."""

from __future__ import annotations

import streamlit as st

from services import (
    config,
    excel_exporter,
    generator,
    genpal,
    plan,
    validators,
)

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _password_gate() -> None:
    expected = config.get_app_password()
    if not expected:
        return
    if st.session_state.get("_genpal_authed"):
        return

    st.markdown("### GenPal Question Bank Factory")
    entered = st.text_input("Prototype access password", type="password")
    if not entered:
        st.stop()
    if entered != expected:
        st.warning("Incorrect password.")
        st.stop()
    st.session_state["_genpal_authed"] = True
    st.rerun()


def _render_sidebar_status() -> None:
    if "_genpal_langsmith_configured" not in st.session_state:
        st.session_state["_genpal_langsmith_configured"] = config.configure_langsmith()

    with st.sidebar:
        st.subheader("Status")
        if st.session_state["_genpal_langsmith_configured"]:
            st.success("LangSmith tracing enabled")
        else:
            st.info("LangSmith tracing not configured")

        if config.use_mock_data():
            st.info("Mock mode: OpenAI calls disabled")
        else:
            st.success("OpenAI configured")

        st.caption(f"Duplicate threshold: {config.get_duplicate_similarity_threshold()}")


def _render_header() -> None:
    st.title("GenPal Question Bank Factory - Prototype")
    st.caption("AI-assisted question bank generation for GenPal-ready Excel output.")
    st.markdown(
        "**How it works**\n"
        "1. Enter skill, SSID, topics, and reference URLs\n"
        "2. Generate one career level at a time with duplicate checks\n"
        "3. Download GenPal-ready Excel (11 columns, Sheet1)"
    )
    if config.use_mock_data():
        st.info("Mock Mode is enabled. No OpenAI API calls will be made.")
    else:
        st.success("Real API Mode is enabled. OpenAI is used for generation and embeddings.")


def _render_mode_and_levels() -> tuple[str, list[str]]:
    mode = st.radio("Generation Mode", options=plan.GENERATION_MODES, index=0, key="genpal_mode")

    if mode == plan.FULL_MODE:
        st.info("Full GenPal Mode generates all 7 career levels × 40 = 280 questions.")
        st.multiselect(
            "Career Levels",
            options=plan.CAREER_LEVELS,
            default=list(plan.CAREER_LEVELS),
            disabled=True,
            key="genpal_levels_full",
        )
        levels = list(plan.CAREER_LEVELS)
    else:
        levels = st.multiselect(
            "Career Levels",
            options=plan.CAREER_LEVELS,
            default=list(plan.DEFAULT_PROTOTYPE_LEVELS),
            key="genpal_levels_proto",
            help="Each selected level generates 40 questions.",
        )

    return mode, levels


def _render_input_form() -> tuple[bool, str, str, str, str]:
    with st.form("genpal_form"):
        skill = st.text_input(
            "Skill Name",
            placeholder="Example: Microsoft SharePoint Server Development",
        )
        ssid = st.text_input(
            "Skill ID / SSID",
            placeholder="Example: 80002591",
            help="Stored in the ssid column on every row.",
        )
        topics_raw = st.text_area(
            "Topic List",
            help="Paste one topic per line. Topic names are preserved exactly.",
            placeholder="Site Collections\nContent Types\nWorkflows\nSearch",
            height=160,
        )
        urls_raw = st.text_area(
            "Reference URL List",
            help="Paste one reference URL per line.",
            placeholder=(
                "https://learn.microsoft.com/en-us/sharepoint/dev/\n"
                "https://learn.microsoft.com/en-us/sharepoint/dev/general-development/"
            ),
            height=160,
        )
        submitted = st.form_submit_button("Generate Question Bank", type="primary")
    return submitted, skill, ssid, topics_raw, urls_raw


def _render_output_panel(mode: str, levels: list[str], skill: str, ssid: str,
                         topics: list[str], urls: list[str]) -> None:
    current = plan.build_plan(mode, levels)
    st.subheader("Expected Output")
    with st.container(border=True):
        st.markdown(f"**Skill Name:** {skill or '—'}")
        st.markdown(f"**Skill ID / SSID:** {ssid or '—'}")
        st.markdown(f"**Mode:** {current.mode}")
        st.markdown(f"**Career levels:** {', '.join(current.levels) if current.levels else '—'}")
        st.markdown(f"**Topics provided:** {len(topics)}")
        st.markdown(f"**Reference URLs provided:** {len(urls)}")
        st.markdown(f"**Questions per level:** {current.per_level}")
        st.markdown(f"**Expected total questions:** {current.total_questions}")
        st.markdown(f"**Duplicate threshold:** {config.get_duplicate_similarity_threshold()}")
        st.markdown(
            "**Output file:** "
            + (plan.build_filename(skill, ssid) if skill and ssid else "—")
        )
        st.markdown(f"**Sheet:** {current.sheet_name}")
        st.markdown(f"**Columns:** {current.column_count}")


def _validate_inputs(mode: str, levels: list[str], skill: str, ssid: str,
                     topics: list[str], urls: list[str]) -> list[str]:
    errors: list[str] = []
    if not skill.strip():
        errors.append("Please enter a Skill Name.")
    if not ssid.strip():
        errors.append("Please enter a Skill ID / SSID.")
    if not topics:
        errors.append("Please enter at least one topic.")
    if not urls:
        errors.append("Please enter at least one reference URL.")
    elif not all(plan.looks_like_url(u) for u in urls):
        errors.append("URLs should look like valid HTTP/HTTPS links.")
    if not levels:
        errors.append("Please select at least one career level.")
    return errors


def _reset_pipeline_state() -> None:
    for key in (
        "_genpal_locked",
        "_genpal_level_dups",
        "_genpal_pending_level",
        "_genpal_pending_count",
        "_genpal_merged",
        "_genpal_global_dups",
        "_genpal_errors",
        "_genpal_xlsx",
        "_genpal_filename",
    ):
        st.session_state.pop(key, None)
    st.session_state["_genpal_locked"] = {}


def _run_pipeline() -> None:
    inputs = st.session_state.get("_genpal_inputs")
    if not inputs:
        return

    skill, ssid = inputs["skill"], inputs["ssid"]
    topics, urls = inputs["topics"], inputs["urls"]
    levels, total = inputs["levels"], inputs["total"]
    threshold = config.get_duplicate_similarity_threshold()
    max_regen = config.get_max_regeneration_attempts()

    locked: dict = st.session_state.setdefault("_genpal_locked", {})
    # Reset transient (recomputed) state each run; keep locked levels.
    for key in ("_genpal_level_dups", "_genpal_pending_level", "_genpal_global_dups",
                "_genpal_errors", "_genpal_merged", "_genpal_xlsx", "_genpal_filename"):
        st.session_state.pop(key, None)

    client = generator.make_client()
    progress = st.progress(0.0, text="Starting generation...")
    done = 0

    try:
        for level in levels:
            if level in locked:
                done += 1
                progress.progress(done / len(levels), text=f"{level}: already locked")
                continue

            def on_batch(label: str, _level=level) -> None:
                progress.progress(done / len(levels), text=f"Generating {label}...")

            # Generate the level once, then surgically regenerate only the
            # colliding rows (feeding every existing question back as an avoid
            # list) until the per-level duplicate check passes or the retry
            # budget is spent. Only then do we block.
            rows = generator.generate_level(
                skill, ssid, level, topics, urls,
                client=client, progress_cb=on_batch,
            )
            rows, dups = genpal.resolve_internal_duplicates(
                rows, threshold,
                topics=topics, urls=urls, client=client, max_attempts=max_regen,
                progress_cb=lambda msg, _l=level: progress.progress(
                    done / len(levels), text=f"{_l}: {msg}..."),
            )

            if dups:
                st.session_state["_genpal_level_dups"] = {level: dups}
                st.session_state["_genpal_pending_level"] = level
                st.session_state["_genpal_pending_count"] = len(rows)
                progress.empty()
                return  # block: auto-regeneration could not clear the duplicates

            locked[level] = rows
            done += 1
            progress.progress(done / len(levels), text=f"{level}: locked ({len(rows)} rows)")

        # All selected levels are locked — merge, title, global check, validate, export.
        # The merged rows are the same dict objects held in ``locked`` (order_and_title
        # mutates in place), so surgically regenerating a duplicate row here also
        # updates the corresponding locked level — no extra bookkeeping needed.
        merged = genpal.finalize(genpal.merge_locked_levels(locked, levels))
        merged, gdups = genpal.resolve_internal_duplicates(
            merged, threshold,
            topics=topics, urls=urls, client=client, max_attempts=max_regen,
            progress_cb=lambda msg: progress.progress(
                done / len(levels), text=f"final 280-row check: {msg}..."),
        )
        st.session_state["_genpal_merged"] = merged

        if gdups:
            st.session_state["_genpal_global_dups"] = gdups
            progress.empty()
            return  # block export only if surgical regeneration could not resolve

        row_errors = validators.validate_rows(
            merged, skill, ssid, topics, urls, expected_count=total
        )
        if row_errors:
            st.session_state["_genpal_errors"] = row_errors
            progress.empty()
            return

        xlsx = excel_exporter.to_xlsx_bytes(merged)
        post_errors = excel_exporter.validate_workbook(xlsx, ssid, total)
        if post_errors:
            st.session_state["_genpal_errors"] = post_errors
            progress.empty()
            return

        st.session_state["_genpal_xlsx"] = xlsx
        st.session_state["_genpal_filename"] = plan.build_filename(skill, ssid)
    except Exception as exc:  # surface API/generation errors without crashing
        st.session_state["_genpal_errors"] = [f"Generation failed: {exc}"]
    finally:
        progress.empty()


def _render_duplicate_findings(findings: list[dict]) -> None:
    with st.expander("Duplicate / Similar Scenario Findings", expanded=True):
        st.warning(f"{len(findings)} similar pair(s) above the threshold.")
        for f in findings:
            st.markdown(
                f"- **Rows {f['row1']} & {f['row2']}** · "
                f"{f['career_level1']}/{f['complexity1']} vs "
                f"{f['career_level2']}/{f['complexity2']} · "
                f"similarity **{f['similarity']}**"
            )
            st.caption(f"Q{f['row1']}: {f['question1']}")
            st.caption(f"Q{f['row2']}: {f['question2']}")


def _render_results() -> None:
    inputs = st.session_state.get("_genpal_inputs")
    if not inputs:
        return

    levels = inputs["levels"]
    locked = st.session_state.get("_genpal_locked", {})
    level_dups = st.session_state.get("_genpal_level_dups", {})
    pending_level = st.session_state.get("_genpal_pending_level")
    global_dups = st.session_state.get("_genpal_global_dups")
    errors = st.session_state.get("_genpal_errors")
    xlsx = st.session_state.get("_genpal_xlsx")
    merged = st.session_state.get("_genpal_merged")

    st.divider()
    st.subheader("Generation progress")
    for level in levels:
        if level in locked:
            st.markdown(f"- {level}: locked ✓ ({len(locked[level])} rows)")
        elif level == pending_level:
            st.markdown(f"- {level}: blocked — duplicates found")
        else:
            st.markdown(f"- {level}: pending")

    # Per-level duplicate block (Check 1).
    if pending_level and level_dups.get(pending_level):
        st.error(
            f"Career level {pending_level} still has similar questions after "
            "automatic regeneration. Resolve before continuing to the next level."
        )
        _render_duplicate_findings(level_dups[pending_level])
        if st.button(f"Regenerate {pending_level}", key="regen_level"):
            st.session_state["_genpal_should_run"] = True
            st.rerun()
        return

    # Global duplicate block (Check 2).
    if global_dups:
        st.error("Final 280-row check found similar questions. Export is blocked.")
        _render_duplicate_findings(global_dups)
        if st.button("Clear all levels and regenerate", key="regen_global"):
            _reset_pipeline_state()
            st.session_state["_genpal_should_run"] = True
            st.rerun()
        return

    # Validation / post-export errors.
    if errors:
        st.error("Validation failed. Export is blocked.")
        for message in errors[:50]:
            st.warning(message)
        if len(errors) > 50:
            st.caption(f"... and {len(errors) - 50} more.")
        if st.button("Clear all levels and regenerate", key="regen_errors"):
            _reset_pipeline_state()
            st.session_state["_genpal_should_run"] = True
            st.rerun()
        return

    # Success — download available.
    if xlsx and merged:
        st.success(f"All checks passed. {len(merged)} questions ready.")
        st.download_button(
            "Download GenPal Excel (.xlsx)",
            data=xlsx,
            file_name=st.session_state.get("_genpal_filename", "genpal_question_bank.xlsx"),
            mime=XLSX_MIME,
            type="primary",
        )
        st.caption(
            f"File: {st.session_state.get('_genpal_filename')} · "
            f"Sheet: {plan.EXCEL_SHEET_NAME} · Columns: {plan.EXCEL_COLUMN_COUNT}"
        )
        st.dataframe(merged[:50], use_container_width=True, hide_index=True)
        if len(merged) > 50:
            st.caption(f"Showing first 50 of {len(merged)} rows. Download for the full bank.")


def main() -> None:
    st.set_page_config(page_title="GenPal Question Bank Factory", layout="wide")
    _password_gate()
    _render_sidebar_status()

    # Run the pipeline once if a submit/regenerate action requested it.
    if st.session_state.pop("_genpal_should_run", False):
        _run_pipeline()

    _render_header()
    st.divider()

    left, right = st.columns([2, 1])
    with left:
        mode, levels = _render_mode_and_levels()
        submitted, skill, ssid, topics_raw, urls_raw = _render_input_form()
        status_area = st.container()
    with right:
        topics_preview = plan.parse_lines(topics_raw)
        urls_preview = plan.parse_lines(urls_raw)
        _render_output_panel(mode, levels, skill.strip(), ssid.strip(),
                             topics_preview, urls_preview)

    if submitted:
        topics = plan.parse_lines(topics_raw)
        urls = plan.parse_lines(urls_raw)
        errors = _validate_inputs(mode, levels, skill, ssid, topics, urls)
        if errors:
            with status_area:
                st.error("Please fix the following before generating:")
                for message in errors:
                    st.warning(message)
        else:
            resolved = plan.build_plan(mode, levels)
            _reset_pipeline_state()
            st.session_state["_genpal_inputs"] = {
                "skill": skill.strip(),
                "ssid": ssid.strip(),
                "topics": topics,
                "urls": urls,
                "mode": resolved.mode,
                "levels": resolved.levels,
                "total": resolved.total_questions,
            }
            st.session_state["_genpal_should_run"] = True
            st.rerun()

    _render_results()


if __name__ == "__main__":
    main()
