// Screen 2 — Documentation Discovery
import { api } from "../api.js";
import { state } from "../state.js";
import {
  el, clear, pageHead, flowStrip, card, badge, button, alert, icon, toast, metric,
} from "../components.js";

function domainOf(url) {
  try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return url || "—"; }
}

export async function render({ navigate }) {
  const jobId = state.get("jobId");
  const root = el("div", { class: "page" });
  root.appendChild(pageHead("Documentation Discovery", "Review and select documentation sources for question generation."));
  root.appendChild(flowStrip(1, ["Input", "Documentation", "Generate", "SME Review", "Export"]));

  if (!jobId) {
    root.appendChild(alert("No active job found. Go back to the Input Form to create one.", "warning"));
    root.appendChild(button("Back to Input", { variant: "outline", onClick: () => navigate("#/") }));
    return root;
  }

  const statusHost = el("div", {});
  root.appendChild(statusHost);
  statusHost.appendChild(el("div", { class: "alert alert-info" },
    el("span", { class: "spin" }, icon("loader")),
    el("div", {}, "Searching latest official documentation…")));

  let job, discovered = [], warning = null;
  try {
    job = state.get("job") || await api.getJob(jobId);
    state.set({ job });
    const res = await api.discoverDocs(jobId);
    discovered = (res.discovered || []).map((d) => ({ ...d, selected: d.selected ?? true }));
    warning = res.warning;
  } catch (e) {
    clear(statusHost).appendChild(alert(e.message, "error"));
    root.appendChild(button("Back to Input", { variant: "outline", onClick: () => navigate("#/") }));
    return root;
  }

  const manualUrls = (job && job.manual_urls) || [];
  clear(statusHost).appendChild(alert(
    `Documentation search complete for ${job.skill_name}.`, "success", "checkCircle"));

  function selectedCount() { return discovered.filter((d) => d.selected).length; }

  // Summary metrics
  const metricsHost = el("div", { class: "grid grid-4" });
  function renderMetrics() {
    clear(metricsHost);
    metricsHost.appendChild(metric(manualUrls.length, "Manual URLs Provided"));
    metricsHost.appendChild(metric(discovered.length, "Auto-Discovered URLs"));
    metricsHost.appendChild(metric(selectedCount() + manualUrls.length, "Selected for Generation", "var(--genpal-purple)"));
    metricsHost.appendChild(el("div", { class: "metric" },
      badge("Ready", "success"), el("div", { class: "m-label mt-1" }, "Documentation Status")));
  }
  renderMetrics();
  root.appendChild(metricsHost);

  // Manual URLs card
  if (manualUrls.length) {
    const list = el("div", { class: "flex-col gap-2" });
    manualUrls.forEach((url) => {
      list.appendChild(el("div", { class: "flex items-center justify-between kv-box", style: "padding:0.5rem 1rem" },
        el("div", { class: "flex items-center gap-2" }, icon("checkCircle", "ico"), el("span", { class: "t-sm t-info" }, url)),
        badge("Always Used", "success")));
    });
    root.appendChild(card({ title: "Manual URLs Provided", body: list }));
  }

  // Discovered docs table
  const tblHost = el("div", {});
  function renderTable() {
    clear(tblHost);
    const head = el("tr", {}, ...["Use", "Source Title", "Domain", "Summary", "URL"].map((h) => el("th", {}, h)));
    const body = el("tbody", {});
    discovered.forEach((d) => {
      const cb = el("input", { class: "checkbox", type: "checkbox", checked: d.selected,
        onchange: () => { d.selected = !d.selected; renderMetrics(); renderHeadCount(); } });
      body.appendChild(el("tr", { class: d.selected ? "" : "dim" },
        el("td", {}, cb),
        el("td", { style: "max-width:180px" }, el("span", { class: "t-xs fw-600 t-dark" }, d.source_name || "Untitled source")),
        el("td", {}, el("span", { class: "t-xs t-secondary" }, domainOf(d.source_url))),
        el("td", { style: "max-width:280px" }, el("span", { class: "t-xs t-muted line-2" }, d.summary || "—")),
        el("td", {}, d.source_url ? el("a", { href: d.source_url, target: "_blank", rel: "noopener", class: "flex items-center gap-1 t-xs" }, icon("external", "ico"), "Open") : "—")));
    });
    tblHost.appendChild(el("div", { class: "tbl-wrap" }, el("table", { class: "tbl" }, el("thead", {}, head), body)));
  }
  let headCountEl;
  function renderHeadCount() { if (headCountEl) headCountEl.textContent = `${selectedCount()} of ${discovered.length} selected`; }
  renderTable();
  headCountEl = el("p", { class: "t-xs t-muted" }, `${selectedCount()} of ${discovered.length} selected`);
  root.appendChild(card({
    title: "Auto-Discovered Documentation",
    headRight: headCountEl,
    body: discovered.length ? tblHost : el("div", { class: "empty-state" }, "No additional documentation discovered. Manual URLs will be used."),
  }));

  if (warning) root.appendChild(alert(warning, "warning"));
  root.appendChild(alert("Web search uses live APIs. If unavailable, only manually provided URLs will be used. You can continue at any time.", "warning"));

  // Actions
  let busy = false;
  async function continueToGen() {
    if (busy) return;
    busy = true;
    try {
      const ids = discovered.filter((d) => d.selected).map((d) => d.source_id);
      await api.selectDocs(jobId, ids);
      toast("Documentation selected.", "success");
      navigate("#/generation");
    } catch (e) {
      toast(e.message, "error"); busy = false;
    }
  }
  root.appendChild(el("div", { class: "flex justify-between" },
    button("Back to Input", { variant: "outline", onClick: () => navigate("#/") }),
    button("Continue to Generation", { variant: "primary", onClick: continueToGen })));

  return root;
}
