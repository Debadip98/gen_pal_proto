// Screen 14 — Business Flow Overview (static informational)
import { el, clear, pageHead, card, button, icon } from "../components.js";

const STEPS = [
  { id: 1, title: "Request Intake", icon: "fileInput", color: "#2563EB",
    desc: "User enters skill, SSID, topics, URLs, counts, and SME email.",
    details: ["Enter Skill Name and SSID", "Add Requestor and SME emails", "Paste topic list (one per line)", "Add reference URLs", "Configure career levels and question counts"] },
  { id: 2, title: "Documentation Enrichment", icon: "search", color: "#4F46E5",
    desc: "System uses pasted URLs and optionally searches latest docs.",
    details: ["Manual URLs always included", "Auto-discovery of latest official docs", "Relevance scoring per source", "User selects final doc set for generation"] },
  { id: 3, title: "AI Question Generation", icon: "loader", color: "#A100FF",
    desc: "System generates QnA records by career level.",
    details: ["Sequential generation by career level", "Configurable question count per level", "Context-rich, role-specific scenarios", "Real-time progress tracking"] },
  { id: 4, title: "Duplicate & Format Validation", icon: "checkCircle", color: "#1E8E3E",
    desc: "System checks schema, duplicates, and similarity.",
    details: ["Embedding-based similarity detection", "Automatic rework for high-similarity pairs", "Schema validation — 11 columns, Sheet1", "Serial numbering and field presence checks"] },
  { id: 5, title: "SME Review", icon: "clipboard", color: "#B45309",
    desc: "SME accepts, rejects, or regenerates each question.",
    details: ["Secure tokenized review link via email", "Question-by-question accept/reject workflow", "LLM suggestion box for each question", "Filter queue by status or alignment"] },
  { id: 6, title: "Question-Level Rework", icon: "refresh", color: "#EA580C",
    desc: "Only selected question is regenerated using SME feedback and docs.",
    details: ["Only one question reworked at a time", "All other questions preserved", "Pre-filled from SME feedback or LLM suggestion", "Side-by-side version comparison"] },
  { id: 7, title: "GenPal Excel Export", icon: "download", color: "#0D9488",
    desc: "System creates one Sheet1 Excel file with 11 columns.",
    details: ["Single workbook, single sheet (Sheet1)", "11 columns in exact order", "No review metadata exported", "Draft and Approved versions available"] },
  { id: 8, title: "Decision Evidence", icon: "dollar", color: "#DB2777",
    desc: "System shows cost, traceability, notifications, and review status.",
    details: ["Detailed API cost breakdown", "LangSmith trace links for observability", "Full duplicate detection findings", "Runtime and performance metrics"] },
];

const BENEFITS = [
  ["Speed", "Generate large question banks in minutes vs. days of manual work."],
  ["Quality", "AI-powered duplicate detection with SME review and LLM suggestions."],
  ["Transparency", "Full cost tracking, traceability, and human review workflow."],
  ["Compliance", "GenPal-validated schema, 11 exact columns, no metadata leakage."],
];

export async function render({ navigate }) {
  const root = el("div", { class: "page" });
  root.appendChild(pageHead("Business Flow Overview", "Executive-friendly visualization of the end-to-end GenPal question bank generation process."));

  let activeStep = null;
  const detailHost = el("div", {});

  const strip = el("div", { class: "flex items-start gap-2", style: "overflow-x:auto;padding-bottom:1rem" });
  function renderStrip() {
    clear(strip);
    STEPS.forEach((s, i) => {
      const active = activeStep === s.id;
      const node = el("button", {
        class: "flex-col items-center gap-2",
        style: `display:flex;width:128px;flex-shrink:0;padding:0.75rem;border-radius:14px;border:2px solid ${active ? "var(--genpal-purple)" : "var(--border)"};background:${active ? "rgba(161,0,255,0.05)" : "#fff"};cursor:pointer`,
        onClick: () => { activeStep = active ? null : s.id; renderStrip(); renderDetail(); },
      },
        (() => { const wrap = el("div", { style: `background:${s.color};border-radius:999px;padding:0.6rem;display:flex` }); const ic = icon(s.icon); ic.style.color = "#fff"; wrap.appendChild(ic); return wrap; })(),
        el("div", { style: "width:20px;height:20px;border-radius:50%;background:var(--border);display:flex;align-items:center;justify-content:center", class: "t-xs t-dark" }, String(s.id)),
        el("p", { class: "t-xs t-dark text-center", style: "line-height:1.2" }, s.title),
        el("p", { class: "t-xs t-muted text-center", style: "line-height:1.2" }, s.desc));
      strip.appendChild(node);
      if (i < STEPS.length - 1) strip.appendChild(el("div", { style: "margin-top:2.5rem;flex-shrink:0" }, icon("arrowRight", "ico")));
    });
  }
  function renderDetail() {
    clear(detailHost);
    if (activeStep == null) return;
    const s = STEPS.find((x) => x.id === activeStep);
    const ul = el("ul", { style: "display:grid;grid-template-columns:1fr 1fr;gap:0.25rem 1.5rem;margin:0;padding:0;list-style:none" });
    s.details.forEach((d) => ul.appendChild(el("li", { class: "flex items-start gap-2 t-xs t-secondary" }, el("span", { class: "t-purple", style: "margin-top:1px" }, "•"), d)));
    detailHost.appendChild(el("div", { style: "margin-top:1rem;border:2px solid var(--genpal-purple);background:var(--surface);border-radius:14px;padding:1.25rem" },
      el("div", { class: "flex items-center gap-3", style: "margin-bottom:0.75rem" },
        (() => { const wrap = el("div", { style: `background:${s.color};border-radius:999px;padding:0.5rem;display:flex` }); const ic = icon(s.icon); ic.style.color = "#fff"; wrap.appendChild(ic); return wrap; })(),
        el("p", { class: "t-sm t-dark" }, `Stage ${s.id}: ${s.title}`)),
      ul));
  }
  renderStrip(); renderDetail();

  root.appendChild(card({
    title: "End-to-End Process",
    desc: "Click any stage to view details.",
    body: el("div", {}, strip, detailHost),
  }));

  const benefits = el("div", { class: "grid grid-4" });
  BENEFITS.forEach(([h, p]) => benefits.appendChild(el("div", { class: "flex-col gap-1" },
    el("h4", { class: "t-sm t-dark fw-600" }, h), el("p", { class: "t-xs t-secondary" }, p))));
  root.appendChild(el("div", { class: "card", style: "border:2px solid var(--genpal-purple)" },
    el("div", { class: "card-head" }, el("div", { class: "card-title" }, "Key Benefits")),
    el("div", { class: "card-body" }, benefits)));

  root.appendChild(el("div", { class: "flex justify-between" },
    button("Back to Cost Summary", { variant: "outline", onClick: () => navigate("#/cost") }),
    button("Back to Home", { variant: "primary", onClick: () => navigate("#/") })));

  return root;
}
