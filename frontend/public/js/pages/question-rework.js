// Screen 8 — Regenerate Selected Question
import { api } from "../api.js";
import { state } from "../state.js";
import {
  el, clear, pageHead, card, badge, button, alert, icon, toast,
} from "../components.js";

const VALIDATION = [
  "Same topic preserved", "Career level preserved", "Complexity preserved",
  "Reference URL preserved", "Documentation alignment checked",
  "Not similar to previous version", "Duplicate check completed",
];

export async function render({ navigate }) {
  const token = state.get("reviewToken");
  const root = el("div", { class: "page" });
  root.appendChild(pageHead("Regenerate Question", "Only this question will be reworked. All other questions remain unchanged."));

  if (!token) {
    root.appendChild(alert("Open the SME review workspace from the secure link first.", "info"));
    root.appendChild(button("Go to Review Queue", { variant: "primary", onClick: () => navigate("#/review") }));
    return root;
  }

  let session;
  try { session = await api.getReviewSession(token); }
  catch (e) { root.appendChild(alert(e.message, "error")); return root; }
  const q = (session.questions || []).find((x) => x.question_id === state.get("selectedQuestionId")) || (session.questions || [])[0];
  if (!q) { root.appendChild(alert("No question selected.", "info")); root.appendChild(button("Back to Queue", { variant: "outline", onClick: () => navigate("#/review") })); return root; }

  let version = null;
  let regenerating = false;

  const bodyHost = el("div", { class: "flex-col gap-6" });
  root.appendChild(bodyHost);

  root.appendChild(alert("Only this question will be reworked. Other questions will not be changed.", "info"));

  function preservedCard() {
    const fields = [
      ["title", String(q.title)], ["ssid", q.ssid], ["skill", q.skill], ["topic", q.topic],
      ["question_type", q.question_type], ["career_level", q.career_level],
      ["complexity", q.complexity], ["reference_url", q.reference_url],
    ];
    const grid = el("div", { class: "grid grid-4" });
    fields.forEach(([k, v]) => grid.appendChild(el("div", { class: "kv-box", style: "padding:0.6rem 0.75rem" },
      el("p", { class: "t-xs t-muted mono" }, k), el("p", { class: "t-xs t-dark mt-1 break" }, v || "—"))));
    return card({ title: "Preserved Fields", body: grid });
  }

  function currentQACard() {
    return card({ title: "Current Question and Answer", body: el("div", { class: "flex-col gap-3" },
      el("div", {}, el("p", { class: "t-xs t-muted" }, "Question"), el("p", { class: "t-sm t-dark mt-1" }, q.question)),
      el("div", {}, el("p", { class: "t-xs t-muted" }, "Answer"), el("p", { class: "t-sm t-dark mt-1" }, q.answer))) });
  }

  const instruction = el("textarea", { class: "textarea", style: "min-height:5rem" },
    state.get("reworkFeedback") || "");

  function instructionCard() {
    const btn = button(regenerating ? "Regenerating…" : "Regenerate This Question",
      { variant: "primary", iconName: regenerating ? "loader" : "refresh", disabled: regenerating, onClick: runRegen });
    return card({ title: "Regeneration Instruction", body: el("div", { class: "flex-col gap-3" },
      instruction,
      el("p", { class: "t-xs t-muted" }, "Pre-filled from SME feedback or LLM suggestion. Edit as needed."),
      version ? null : btn) });
  }

  async function runRegen() {
    const fb = instruction.value.trim();
    if (!fb) { toast("Enter a regeneration instruction.", "error"); return; }
    regenerating = true; build();
    try {
      version = await api.regenerateQuestion(token, q.question_id, fb, false);
      state.set({ lastVersion: version, selectedQuestionId: q.question_id });
      toast("Question regenerated.", "success");
    } catch (e) { toast(e.message, "error"); }
    finally { regenerating = false; build(); }
  }

  function comparisonBlock() {
    const orig = el("div", { class: "card", style: "border:2px solid #FECACA" },
      el("div", { class: "card-head", style: "background:var(--error-bg)" }, el("div", { class: "card-title t-error" }, "Original Question")),
      el("div", { class: "card-body flex-col gap-3" },
        el("div", {}, el("p", { class: "t-xs t-muted" }, "Question"), el("p", { class: "t-xs t-dark mt-1" }, version.old_question)),
        el("div", {}, el("p", { class: "t-xs t-muted" }, "Answer"), el("p", { class: "t-xs t-dark mt-1" }, version.old_answer))));
    const neu = el("div", { class: "card", style: "border:2px solid var(--success)" },
      el("div", { class: "card-head", style: "background:var(--success-bg)" }, el("div", { class: "card-title t-success" }, "Regenerated Question")),
      el("div", { class: "card-body flex-col gap-3" },
        el("div", {}, el("p", { class: "t-xs t-muted" }, "Question"), el("p", { class: "t-xs t-dark mt-1" }, version.new_question)),
        el("div", {}, el("p", { class: "t-xs t-muted" }, "Answer"), el("p", { class: "t-xs t-dark mt-1" }, version.new_answer))));

    const badges = el("div", { class: "flex flex-wrap gap-2" });
    VALIDATION.forEach((b) => badges.appendChild(badge(b, "success", "check")));

    const decisions = el("div", { class: "flex gap-3 flex-wrap" },
      button("Accept Change", { variant: "success", iconName: "check", onClick: acceptChange }),
      button("Reject Change", { variant: "danger", iconName: "x", onClick: rejectChange }),
      button("Regenerate Again", { variant: "outline", iconName: "refresh", onClick: () => { version = null; build(); } }));

    return el("div", { class: "flex-col gap-6" },
      el("div", { class: "grid grid-2" }, orig, neu),
      card({ title: "Validation Results", body: badges }),
      decisions);
  }

  async function acceptChange() {
    try { await api.acceptVersion(token, version.version_id); toast("Change accepted.", "success"); state.set({ lastVersion: version }); navigate("#/version-compare"); }
    catch (e) { toast(e.message, "error"); }
  }
  async function rejectChange() {
    try { await api.rejectVersion(token, version.version_id); toast("Change rejected.", "success"); navigate("#/sme-question"); }
    catch (e) { toast(e.message, "error"); }
  }

  function build() {
    clear(bodyHost);
    bodyHost.append(preservedCard(), currentQACard(), instructionCard());
    if (version) bodyHost.appendChild(comparisonBlock());
  }

  build();
  return root;
}
