// Screen 13 — Cost & Traceability Summary
import { api } from "../api.js";
import { state } from "../state.js";
import {
  el, pageHead, card, badge, button, alert, icon, metric,
} from "../components.js";

function usd(n) {
  const v = Number(n || 0);
  return `$${v.toFixed(v < 1 ? 4 : 2)}`;
}
function num(n) { return Number(n || 0).toLocaleString(); }

// by_step / by_model may map name -> number, or name -> { estimated_cost, ... }.
function breakdownRows(obj) {
  const out = [];
  for (const [name, val] of Object.entries(obj || {})) {
    if (val && typeof val === "object") {
      const cost = val.estimated_cost ?? val.cost ?? val.estimated_cost_usd ?? 0;
      const tokens = val.tokens ?? (val.input_tokens || 0) + (val.output_tokens || 0) + (val.embedding_tokens || 0);
      out.push({ name, cost, tokens, calls: val.calls ?? val.count ?? val.events ?? null });
    } else {
      out.push({ name, cost: val, tokens: null, calls: null });
    }
  }
  return out;
}

export async function render({ navigate }) {
  const jobId = state.get("jobId");
  const root = el("div", { class: "page" });
  root.appendChild(pageHead("Cost & Traceability Summary", "Detailed breakdown of API costs and observability metrics."));

  if (!jobId) {
    root.appendChild(alert("No active job. Generate a question bank first.", "warning"));
    root.appendChild(button("Back to Input", { variant: "outline", onClick: () => navigate("#/") }));
    return root;
  }

  let cost;
  try { cost = await api.getCostSummary(jobId); }
  catch (e) { root.appendChild(alert(e.message, "error")); return root; }

  const totalTokens = (cost.total_input_tokens || 0) + (cost.total_output_tokens || 0) + (cost.total_embedding_tokens || 0);
  const totalQ = (state.get("dashboard") && state.get("dashboard").total_questions) || (state.get("job") && state.get("job").generated_count) || 0;
  const perQuestion = totalQ ? (cost.total_estimated_cost_usd || 0) / totalQ : 0;

  // Top metrics
  const mGrid = el("div", { class: "grid grid-4" });
  [
    ["Total Estimated Cost", usd(cost.total_estimated_cost_usd), "var(--genpal-purple)"],
    ["Input Tokens", num(cost.total_input_tokens)],
    ["Output Tokens", num(cost.total_output_tokens)],
    ["Embedding Tokens", num(cost.total_embedding_tokens)],
    ["Total Tokens", num(totalTokens)],
    ["Total Events", num(cost.total_events)],
    ["Cost / Question", usd(perQuestion)],
    ["LangSmith", state.get("mockMode") ? "Mock" : "Live", "var(--info)"],
  ].forEach(([l, v, c]) => mGrid.appendChild(metric(v, l, c)));
  root.appendChild(mGrid);

  // Breakdown tables
  function breakdownCard(title, iconName, obj) {
    const rows = breakdownRows(obj);
    const body = rows.length
      ? el("div", { class: "tbl-wrap" },
          el("table", { class: "tbl" },
            el("thead", {}, el("tr", {}, el("th", {}, "Name"), el("th", {}, "Tokens"), el("th", {}, "Calls"), el("th", {}, "Est. Cost"))),
            el("tbody", {}, ...rows.map((r) =>
              el("tr", {},
                el("td", { class: "t-sm t-dark" }, r.name),
                el("td", { class: "t-sm" }, r.tokens == null ? "—" : num(r.tokens)),
                el("td", { class: "t-sm" }, r.calls == null ? "—" : num(r.calls)),
                el("td", { class: "t-sm t-dark" }, usd(r.cost)))))))
      : el("div", { class: "empty-state" }, "No usage recorded yet.");
    return card({ title, headRight: icon(iconName), body });
  }

  root.appendChild(el("div", { class: "grid grid-2" },
    breakdownCard("Cost by Step", "loader", cost.by_step),
    breakdownCard("Cost by Model", "dollar", cost.by_model)));

  // Hero total
  root.appendChild(el("div", { class: "card", style: "border:2px solid var(--genpal-purple)" },
    el("div", { class: "card-body flex items-center justify-between" },
      el("div", { class: "flex items-center gap-3" },
        el("div", { style: "background:var(--genpal-purple);border-radius:999px;padding:0.9rem;display:flex", class: "" },
          (() => { const i = icon("dollar"); i.style.color = "#fff"; i.setAttribute("width", "28"); i.setAttribute("height", "28"); return i; })()),
        el("div", {},
          el("p", { class: "t-xs t-muted" }, "Total Estimated Cost"),
          el("p", { class: "t-2xl fw-600 t-dark" }, usd(cost.total_estimated_cost_usd)))),
      el("div", { class: "text-center" },
        el("p", { class: "t-xs t-muted" }, "Cost per Question"),
        el("p", { class: "t-xl t-dark" }, usd(perQuestion))))));

  root.appendChild(el("div", { class: "flex justify-between" },
    button("Back to Export", { variant: "outline", onClick: () => navigate("#/export") }),
    button("View Business Flow", { variant: "primary", onClick: () => navigate("#/flow") })));

  return root;
}
