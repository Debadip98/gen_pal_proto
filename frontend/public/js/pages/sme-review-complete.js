// Screen 11 — SME Final Review Complete
import { api } from "../api.js";
import { state } from "../state.js";
import {
  el, pageHead, card, badge, button, alert, icon, metric, toast,
} from "../components.js";

const PENDING = new Set(["PENDING_SME_REVIEW", "PENDING_REVIEW", "DRAFT"]);

export async function render({ navigate }) {
  const token = state.get("reviewToken");
  const root = el("div", { class: "page" });
  root.appendChild(pageHead("Review Complete", "SME review has concluded. Review the final status before exporting."));

  if (!token) {
    root.appendChild(alert("Open the SME review workspace from the secure link first.", "info"));
    root.appendChild(button("Go to Review Queue", { variant: "primary", onClick: () => navigate("#/review") }));
    return root;
  }

  let session;
  try { session = await api.getReviewSession(token); state.set({ jobId: session.job_id }); }
  catch (e) { root.appendChild(alert(e.message, "error")); return root; }

  const questions = session.questions || [];
  const total = questions.length;
  const accepted = questions.filter((q) => q.status === "ACCEPTED").length;
  const rejected = questions.filter((q) => q.status === "REJECTED").length;
  const regenerated = questions.filter((q) => q.status === "REGENERATED").length;
  const pending = questions.filter((q) => PENDING.has(q.status)).length;
  const dupResolved = questions.filter((q) => q.duplicate_warning).length;
  const allDone = total > 0 && pending === 0 && rejected === 0;
  const completionPct = total ? Math.round(((accepted + rejected) / total) * 100) : 0;

  // Metrics
  const mGrid = el("div", { class: "grid grid-6" });
  mGrid.append(
    metric(total, "Total Questions"),
    metric(accepted, "Accepted", "var(--success)"),
    metric(rejected, "Rejected", "var(--error)"),
    metric(regenerated, "Regenerated", "var(--warning)"),
    metric(pending, "Pending"),
    metric(allDone ? "No" : "—", "Manual Override", "var(--success)"));
  root.appendChild(mGrid);

  // Status banner
  if (allDone) {
    root.appendChild(el("div", { class: "card", style: "border:1px solid var(--success);background:var(--success-bg)" },
      el("div", { class: "card-body flex items-center gap-4" },
        el("div", { style: "background:var(--success);border-radius:999px;padding:0.75rem;display:flex" },
          (() => { const i = icon("checkCircle"); i.style.color = "#fff"; return i; })()),
        el("div", {},
          el("p", { class: "t-lg fw-600", style: "color:#065F46" }, "All questions are approved for export."),
          el("p", { class: "t-sm", style: "color:#065F46" }, "The GenPal-ready Excel file is ready for download.")))));
  } else {
    root.appendChild(el("div", { class: "card", style: "border:1px solid var(--warning);background:var(--warning-bg)" },
      el("div", { class: "card-body flex-col gap-3" },
        el("div", { class: "flex items-center gap-3" }, icon("alert"), el("p", { class: "t-sm", style: "color:#92400E" }, `${pending} question(s) pending and ${rejected} rejected. Resolve these or download a draft.`)),
        el("div", { class: "flex gap-3" },
          button("Continue Review", { variant: "outline", sm: true, onClick: () => navigate("#/review") }),
          button("Download Draft Excel", { variant: "outline", sm: true, iconName: "download", onClick: () => api.exportExcel(session.job_id, "draft") })))));
  }

  // Review summary
  root.appendChild(card({
    title: "Review Summary",
    body: el("div", { class: "grid grid-2" },
      el("div", { class: "flex-col gap-2" },
        sumRow("Skill", session.skill_name),
        sumRow("SSID", session.ssid),
        sumRow("Total Questions", String(total)),
        sumRow("SME Reviewer", session.sme_email)),
      el("div", { class: "flex-col gap-2" },
        sumRow("Review Completion", `${completionPct}%`),
        sumRow("Regenerated Questions", String(regenerated)),
        sumRow("Duplicate Warnings", String(dupResolved)),
        sumRowNode("Export Readiness", allDone ? badge("Ready", "success") : badge("Draft only", "outline-amber")))),
  }));

  root.appendChild(el("div", { class: "flex justify-between" },
    button("Back to Review Queue", { variant: "outline", onClick: () => navigate("#/review") }),
    el("div", { class: "flex gap-3" },
      button("Notify Requestor", { variant: "outline", iconName: "mail", onClick: () => toast("Requestor notifications are sent automatically as you accept/reject.", "info") }),
      button("Download GenPal Import Excel", { variant: "primary", iconName: "download", disabled: !allDone, onClick: () => { api.exportExcel(session.job_id, "approved"); toast("Approved Excel download started.", "success"); } }))));

  return root;
}

function sumRow(k, v) {
  return el("div", { class: "flex justify-between t-sm" }, el("span", { class: "t-muted" }, k), el("span", { class: "t-dark break" }, v || "—"));
}
function sumRowNode(k, node) {
  return el("div", { class: "flex justify-between items-center t-sm" }, el("span", { class: "t-muted" }, k), node);
}
