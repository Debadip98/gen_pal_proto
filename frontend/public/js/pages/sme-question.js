// Screen 7 — SME Question Review Detail
import { api } from "../api.js";
import { state } from "../state.js";
import {
  el, clear, pageHead, card, badge, button, alert, icon, toast,
} from "../components.js";
import { questionStatusBadge } from "./_shared.js";

const SUGGESTION_LABELS = {
  quality_summary: "Quality Summary",
  possible_concern: "Possible Concern",
  suggested_improvement: "Suggested Improvement",
  doc_alignment: "Documentation Alignment",
  recommended_action: "Recommended Action",
  sme_message: "SME-Friendly Message",
  sme_friendly_message: "SME-Friendly Message",
  message: "SME-Friendly Message",
};

export async function render({ navigate }) {
  const token = state.get("reviewToken");
  const root = el("div", { class: "page" });

  if (!token) {
    root.appendChild(pageHead("Question Review"));
    root.appendChild(alert("Open the SME review workspace from the secure link first.", "info"));
    root.appendChild(button("Go to Review Queue", { variant: "primary", onClick: () => navigate("#/review") }));
    return root;
  }

  let session;
  try { session = await api.getReviewSession(token); state.set({ reviewSession: session }); }
  catch (e) { root.appendChild(alert(e.message, "error")); return root; }

  const questions = session.questions || [];
  if (!questions.length) {
    root.appendChild(pageHead("Question Review"));
    root.appendChild(alert("No questions in this review session.", "info"));
    return root;
  }

  let idx = Math.max(0, questions.findIndex((q) => q.question_id === state.get("selectedQuestionId")));
  let busy = false;

  function current() { return questions[idx]; }

  function go(delta) {
    idx = (idx + delta + questions.length) % questions.length;
    state.set({ selectedQuestionId: current().question_id });
    build();
  }

  async function doAccept() {
    if (busy) return; busy = true;
    try { await api.acceptQuestion(token, current().question_id); current().status = "ACCEPTED"; toast("Question accepted.", "success"); nextPendingOrQueue(); }
    catch (e) { toast(e.message, "error"); busy = false; }
  }
  async function doReject() {
    if (busy) return;
    const comment = feedbackEl.value.trim();
    if (!comment) { toast("Add feedback before rejecting.", "error"); return; }
    busy = true;
    try { await api.rejectQuestion(token, current().question_id, comment); current().status = "REJECTED"; toast("Question rejected. Feedback saved.", "success"); build(); }
    catch (e) { toast(e.message, "error"); }
    finally { busy = false; }
  }
  function doRegenerate() {
    state.set({ selectedQuestionId: current().question_id, reworkFeedback: feedbackEl.value.trim() });
    navigate("#/regenerate");
  }
  function nextPendingOrQueue() {
    busy = false;
    const next = questions.findIndex((q, i) => i > idx && ["PENDING_SME_REVIEW", "PENDING_REVIEW", "DRAFT"].includes(q.status));
    if (next >= 0) { idx = next; state.set({ selectedQuestionId: current().question_id }); build(); }
    else { toast("Reached end of queue.", "info"); build(); }
  }

  let suggestionHost, feedbackEl;

  function parsedSuggestion(q) {
    if (!q.llm_review_message) return null;
    try { return JSON.parse(q.llm_review_message); } catch { return null; }
  }

  function renderSuggestion(q) {
    clear(suggestionHost);
    const sug = parsedSuggestion(q);
    if (!sug) {
      suggestionHost.appendChild(el("div", { class: "flex-col gap-3" },
        el("p", { class: "t-xs t-muted" }, "No LLM review yet for this question."),
        button("Get LLM Suggestion", { variant: "outline", sm: true, iconName: "refresh", onClick: async () => {
          try { const res = await api.generateSuggestion(token, q.question_id); q.llm_review_message = JSON.stringify(res.suggestion || {}); renderSuggestion(q); toast("LLM review generated.", "success"); }
          catch (e) { toast(e.message, "error"); }
        } })));
      return;
    }
    const items = Object.entries(sug).filter(([, v]) => v != null && v !== "");
    items.forEach(([k, v]) => {
      suggestionHost.appendChild(el("div", { class: "flex-col gap-1" },
        el("p", { class: "t-xs t-muted" }, SUGGESTION_LABELS[k] || k),
        el("p", { class: "t-xs t-dark" }, typeof v === "string" ? v : JSON.stringify(v))));
    });
    const improvement = sug.suggested_improvement || sug.recommended_action || "";
    suggestionHost.appendChild(button("Use Suggestion for Regeneration", { variant: "outline", sm: true, block: true, iconName: "refresh", onClick: () => {
      state.set({ selectedQuestionId: q.question_id, reworkFeedback: improvement });
      navigate("#/regenerate");
    } }));
  }

  function build() {
    clear(root);
    const q = current();
    root.appendChild(el("div", { class: "flex items-center justify-between" },
      el("div", { class: "page-head" },
        el("h2", { class: "page-title" }, "Question Review"),
        el("p", { class: "page-sub" }, `Question ${idx + 1} of ${questions.length} — ${q.topic || ""}`)),
      button("Back to Queue", { variant: "outline", sm: true, onClick: () => navigate("#/review") })));

    // metadata
    root.appendChild(card({
      body: el("div", { class: "grid", style: "grid-template-columns:repeat(7,1fr)" },
        meta("title", String(q.title)),
        meta("topic", q.topic),
        metaNode("career_level", badge(q.career_level, "outline")),
        metaNode("complexity", badge(q.complexity, "gray")),
        metaNode("reference_url", el("span", { class: "t-xs t-info break" }, q.reference_url || "—")),
        metaNode("duplicate_warning", q.duplicate_warning ? badge("Yes", "outline-amber") : badge("No", "outline")),
        metaNode("status", questionStatusBadge(q.status))),
    }));

    feedbackEl = el("textarea", { class: "textarea", style: "min-height:6rem",
      placeholder: "Add feedback to guide rejection or regeneration of this question." },
      state.get("reworkFeedback") && state.get("selectedQuestionId") === q.question_id ? state.get("reworkFeedback") : "");

    const left = el("div", { class: "flex-col gap-4" },
      card({ title: "Question", body: el("p", { class: "t-sm t-dark", style: "line-height:1.6" }, q.question) }),
      card({ title: "Answer", body: el("p", { class: "t-sm t-dark", style: "line-height:1.6" }, q.answer) }),
      card({ title: "SME Feedback / Review Instruction", body: el("div", { class: "flex-col gap-2" },
        feedbackEl, el("p", { class: "t-xs t-muted" }, "Your feedback will be used to regenerate this question if you choose to rework it.")) }),
      el("div", { class: "flex gap-3 flex-wrap" },
        button("Accept Question", { variant: "success", iconName: "check", disabled: busy, onClick: doAccept }),
        button("Reject Question", { variant: "danger", iconName: "x", disabled: busy, onClick: doReject }),
        button("Regenerate Question", { variant: "outline", iconName: "refresh", disabled: busy, onClick: doRegenerate })));

    suggestionHost = el("div", { class: "flex-col gap-4" });
    const right = el("div", { class: "card", style: "border:1px solid var(--genpal-purple)" },
      el("div", { class: "card-head", style: "background:rgba(161,0,255,0.05)" },
        el("div", { class: "card-title flex items-center gap-2" }, icon("refresh"), "LLM Review Suggestion")),
      el("div", { class: "card-body" }, suggestionHost));
    renderSuggestion(q);

    root.appendChild(el("div", { class: "grid", style: "grid-template-columns:2fr 1fr" }, left, right));

    root.appendChild(el("div", { class: "flex justify-between" },
      button("Previous Question", { variant: "outline", sm: true, onClick: () => go(-1) }),
      button("Next Question", { variant: "outline", sm: true, onClick: () => go(1) })));
  }

  build();
  return root;
}

function meta(label, value) {
  return el("div", {}, el("p", { class: "t-xs t-muted mono" }, label), el("div", { class: "t-sm mt-1 break" }, value || "—"));
}
function metaNode(label, node) {
  return el("div", {}, el("p", { class: "t-xs t-muted mono" }, label), el("div", { class: "mt-1" }, node));
}
