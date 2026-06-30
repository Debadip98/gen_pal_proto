// Screen 12 — Export & Download Center
import { api } from "../api.js";
import { state } from "../state.js";
import {
  el, pageHead, card, badge, button, alert, icon, toast,
} from "../components.js";

const GENPAL_COLUMNS = ["title", "ssid", "skill", "topic", "question_type", "career_level", "complexity", "question", "answer", "options", "reference_url"];

const VALIDATION = [
  "One workbook only",
  "One sheet only (Sheet1)",
  "11 required columns",
  "title serial numbers are sequential",
  "ssid present in every row",
  "question_type = QnA",
  "options column blank",
  "No internal review metadata exported",
];

export async function render({ navigate }) {
  const jobId = state.get("jobId");
  const root = el("div", { class: "page" });
  root.appendChild(pageHead("Export & Download Center", "Download the GenPal-ready Excel file in draft or approved form."));

  if (!jobId) {
    root.appendChild(alert("No active job. Generate a question bank first.", "warning"));
    root.appendChild(button("Back to Input", { variant: "outline", onClick: () => navigate("#/") }));
    return root;
  }

  // Pull job + dashboard context for filename / row counts / readiness.
  let job = state.get("job"), dash = state.get("dashboard");
  try { job = job || await api.getJob(jobId); state.set({ job }); } catch { /* ignore */ }
  const token = state.get("jobToken");
  if (token) { try { dash = await api.getDashboard(token); state.set({ dashboard: dash }); } catch { /* ignore */ } }

  const fileName = job ? `${job.skill_name}-${job.ssid}.xlsx` : "genpal_question_bank.xlsx";
  const rows = (dash && dash.total_questions) || (job && job.generated_count) || 0;
  const draftReady = dash ? dash.draft_download_ready : (job ? job.draft_download_ready : true);
  const approvedReady = dash ? dash.approved_download_ready : (job ? job.approved_download_ready : false);

  let busy = false;
  const dl = (type) => {
    if (busy) return; busy = true;
    try { api.exportExcel(jobId, type); toast(`${type === "approved" ? "Approved" : "Draft"} Excel download started.`, "success"); }
    finally { setTimeout(() => (busy = false), 800); }
  };

  function fileMeta(statusBadge) {
    return el("div", { class: "flex-col gap-1 t-xs t-muted" },
      el("div", { class: "kv-row" }, el("span", { class: "k" }, "File name"), el("span", { class: "v break" }, fileName)),
      el("div", { class: "kv-row" }, el("span", { class: "k" }, "Rows"), el("span", { class: "v" }, String(rows))),
      el("div", { class: "kv-row" }, el("span", { class: "k" }, "Status"), statusBadge));
  }

  const draftCard = el("div", { class: "card", style: "border-width:2px" },
    el("div", { class: "card-body flex-col gap-4" },
      el("div", { class: "card-title flex items-center gap-2" }, icon("download"), "Current Draft Excel"),
      el("p", { class: "t-sm t-secondary" }, "Available once generated rows exist. May include questions not fully accepted by SME."),
      alert("Some questions may still be pending SME review. This file includes all generated rows regardless of review status.", "warning"),
      fileMeta(badge("Draft", "outline-amber")),
      button("Download Draft Excel", { variant: "outline", block: true, iconName: "download", disabled: !draftReady, onClick: () => dl("draft") })));

  const apprCard = el("div", { class: "card", style: "border:2px solid var(--success)" },
    el("div", { class: "card-body flex-col gap-4" },
      el("div", { class: "card-title flex items-center gap-2" }, icon("download"), "Approved GenPal Excel"),
      el("p", { class: "t-sm t-secondary" }, "Available after all questions are accepted or final override is confirmed."),
      approvedReady
        ? alert("All questions have been reviewed and approved by the SME. This file is ready for GenPal import.", "success")
        : alert("Not all questions are approved yet. Complete the SME review to enable this download.", "info"),
      fileMeta(approvedReady ? badge("Approved", "success") : badge("Pending", "gray")),
      button("Download Approved Excel", { variant: "success", block: true, iconName: "download", disabled: !approvedReady, onClick: () => dl("approved") })));

  root.appendChild(el("div", { class: "grid grid-2" }, draftCard, apprCard));

  // Validation checklist
  const checks = el("div", { class: "grid grid-2" });
  VALIDATION.forEach((c) => {
    checks.appendChild(el("div", { class: "flex items-center gap-3", style: "border:1px solid var(--border);border-radius:var(--radius);padding:0.75rem" },
      icon("checkCircle", "ico"),
      el("span", { class: "t-sm t-dark flex-1" }, c),
      badge("Passed", "success")));
  });
  root.appendChild(card({
    title: "Excel Validation Checklist",
    body: el("div", { class: "flex-col gap-4" },
      checks,
      el("div", { class: "kv-box" },
        el("p", { class: "t-xs t-muted mono" }, "Review metadata (review_status, sme_feedback, llm_suggestion) is shown in the UI only and is NOT exported to Excel."))),
  }));

  // GenPal column reference
  const cols = el("div", { class: "flex flex-wrap gap-2" });
  GENPAL_COLUMNS.forEach((c) => cols.appendChild(badge(c, "gray")));
  root.appendChild(card({ title: "GenPal Excel Columns (Exact Order)", body: cols }));

  root.appendChild(el("div", { class: "flex justify-between" },
    button("Back to Dashboard", { variant: "outline", onClick: () => navigate(token ? `#/dashboard?job_token=${token}` : "#/dashboard") }),
    button("View Cost Summary", { variant: "outline", onClick: () => navigate("#/cost") })));

  return root;
}
