// Screen 6 — SME Review Workspace (queue)
import { api } from "../api.js";
import { state } from "../state.js";
import {
  el, clear, pageHead, card, badge, button, alert, icon, metric, toast,
} from "../components.js";
import { questionStatusBadge } from "./_shared.js";

const PENDING = new Set(["PENDING_SME_REVIEW", "PENDING_REVIEW", "DRAFT"]);
const CHIPS = ["All", "Pending", "Accepted", "Rejected", "Regenerated", "Manual Review Required", "Duplicate Warning", "Doc Alignment Warning"];

function alignmentBadge(a) {
  if (a === "ALIGNED") return badge("Aligned", "success");
  if (a === "PARTIALLY_ALIGNED") return badge("Partial", "outline-amber");
  if (a === "NOT_ALIGNED") return badge("Not Aligned", "outline-red");
  return badge("—", "outline");
}

export async function render({ navigate, query }) {
  const token = query.review_token || state.get("reviewToken");
  const root = el("div", { class: "page" });
  root.appendChild(pageHead("SME Review Workspace", "Review generated GenPal QnA questions — accept, reject, or regenerate individual items."));

  if (!token) {
    root.appendChild(alert("Open this workspace from the secure SME review link, or paste a review token below.", "info"));
    const input = el("input", { class: "input", placeholder: "Paste review token" });
    root.appendChild(el("div", { class: "flex gap-2", style: "max-width:520px" }, input,
      button("Open", { variant: "primary", onClick: () => { if (input.value.trim()) navigate(`#/review?review_token=${input.value.trim()}`); } })));
    return root;
  }

  let session;
  try { session = await api.getReviewSession(token); state.set({ reviewToken: token, reviewSession: session, jobId: session.job_id }); }
  catch (e) { root.appendChild(alert(e.message, "error")); return root; }

  const questions = session.questions || [];
  const counts = {
    pending: questions.filter((q) => PENDING.has(q.status)).length,
    accepted: questions.filter((q) => q.status === "ACCEPTED").length,
    rejected: questions.filter((q) => q.status === "REJECTED").length,
    regenerated: questions.filter((q) => q.status === "REGENERATED").length,
    manual: questions.filter((q) => q.status === "MANUAL_REVIEW_REQUIRED").length,
  };

  // Job summary
  root.appendChild(card({
    body: el("div", { class: "grid grid-6" },
      sumItem("Skill Name", session.skill_name),
      sumItem("SSID", session.ssid),
      sumItem("Total Questions", String(session.total_questions)),
      sumItem("SME", session.sme_email),
      sumItem("Review Due", session.expires_at ? new Date(session.expires_at).toLocaleDateString() : "—"),
      sumItemNode("Review Status", badge("In Progress", "outline-amber"))),
  }));

  // Progress metrics
  const mGrid = el("div", { class: "grid grid-5" });
  mGrid.append(
    metric(counts.pending, "Pending"),
    metric(counts.accepted, "Accepted", "var(--success)"),
    metric(counts.rejected, "Rejected", "var(--error)"),
    metric(counts.regenerated, "Regenerated", "var(--warning)"),
    metric(counts.manual, "Manual Review", "var(--error)"));
  root.appendChild(mGrid);

  // Filter chips + table
  let activeFilter = "All";
  const chipRow = el("div", { class: "flex flex-wrap gap-2" });
  const tableHost = el("div", {});

  function applyFilter(list) {
    switch (activeFilter) {
      case "Pending": return list.filter((q) => PENDING.has(q.status));
      case "Accepted": return list.filter((q) => q.status === "ACCEPTED");
      case "Rejected": return list.filter((q) => q.status === "REJECTED");
      case "Regenerated": return list.filter((q) => q.status === "REGENERATED");
      case "Manual Review Required": return list.filter((q) => q.status === "MANUAL_REVIEW_REQUIRED");
      case "Duplicate Warning": return list.filter((q) => q.duplicate_warning);
      case "Doc Alignment Warning": return list.filter((q) => ["PARTIALLY_ALIGNED", "NOT_ALIGNED"].includes(q.doc_alignment_status));
      default: return list;
    }
  }

  function renderChips() {
    clear(chipRow);
    CHIPS.forEach((chip) => {
      const active = activeFilter === chip;
      chipRow.appendChild(el("button", {
        class: "badge " + (active ? "badge-purple" : "badge-outline"),
        style: "cursor:pointer;padding:0.3rem 0.7rem",
        onClick: () => { activeFilter = chip; renderChips(); renderTable(); },
      }, chip));
    });
  }

  function renderTable() {
    clear(tableHost);
    const filtered = applyFilter(questions);
    const body = el("tbody", {});
    filtered.forEach((q) => {
      body.appendChild(el("tr", {},
        el("td", {}, String(q.title)),
        el("td", { style: "max-width:160px" }, el("p", { class: "t-xs line-2" }, q.topic || "—")),
        el("td", {}, badge(q.career_level, "outline")),
        el("td", { class: "t-xs" }, q.complexity),
        el("td", {}, questionStatusBadge(q.status)),
        el("td", {}, q.duplicate_warning ? icon("alert", "ico") : el("span", { class: "t-xs t-muted" }, "—")),
        el("td", {}, alignmentBadge(q.doc_alignment_status)),
        el("td", {}, button("Review", { variant: "outline", sm: true, onClick: () => { state.set({ selectedQuestionId: q.question_id }); navigate("#/sme-question"); } }))));
    });
    const tbl = el("div", { class: "tbl-wrap" },
      el("table", { class: "tbl" },
        el("thead", {}, el("tr", {}, ...["title", "topic", "career_level", "complexity", "status", "dup warning", "doc alignment", "action"].map((h) => el("th", {}, h)))),
        body));
    tableHost.appendChild(filtered.length ? tbl : el("div", { class: "empty-state" }, "No questions match this filter."));
  }

  renderChips(); renderTable();
  root.appendChild(chipRow);
  root.appendChild(card({ title: "Question Review Queue", body: tableHost }));

  root.appendChild(el("div", { class: "flex justify-end" },
    button("Start Review", { variant: "primary", iconName: "clipboard", onClick: () => {
      const first = questions.find((q) => PENDING.has(q.status)) || questions[0];
      if (first) { state.set({ selectedQuestionId: first.question_id }); navigate("#/sme-question"); }
      else toast("No questions to review.", "info");
    } })));

  return root;
}

function sumItem(label, value) {
  return el("div", {}, el("p", { class: "t-xs t-muted" }, label), el("div", { class: "t-sm t-dark mt-1 break" }, value || "—"));
}
function sumItemNode(label, node) {
  return el("div", {}, el("p", { class: "t-xs t-muted" }, label), el("div", { class: "mt-1" }, node));
}
