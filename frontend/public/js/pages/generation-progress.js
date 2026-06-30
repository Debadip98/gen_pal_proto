// Screen 3 — Generation Progress
import { api } from "../api.js";
import { state } from "../state.js";
import {
  el, clear, pageHead, flowStrip, card, badge, button, alert, icon, metric, progressBar,
} from "../components.js";

const RUNNING = new Set(["DRAFT", "GENERATING"]);
const DONE = new Set(["GENERATED", "SENT_TO_SME", "IN_REVIEW", "APPROVED", "EXCEL_READY", "EXPORTED"]);

export async function render({ navigate }) {
  const jobId = state.get("jobId");
  const root = el("div", { class: "page" });
  root.appendChild(pageHead("Generation Progress", "Sequential question generation by career level with duplicate detection."));
  root.appendChild(flowStrip(2, ["Input", "Documentation", "Generate", "SME Review", "Export"]));

  if (!jobId) {
    root.appendChild(alert("No active job found. Go back to the Input Form to create one.", "warning"));
    root.appendChild(button("Back to Input", { variant: "outline", onClick: () => navigate("#/") }));
    return root;
  }

  const bannerHost = el("div", {});
  const metricsHost = el("div", { class: "grid grid-5" });
  const detailHost = el("div", {});
  const actionsHost = el("div", { class: "flex gap-3" });
  root.append(bannerHost, metricsHost, detailHost, actionsHost);

  let interval = null;
  let started = false;
  let navigated = false;

  function stop() { if (interval) { clearInterval(interval); interval = null; } }

  function paint(job, errMsg) {
    if (errMsg) clear(bannerHost).appendChild(alert(errMsg, "error"));
    const status = job ? job.status : "—";
    const total = job ? job.total_expected_questions : 0;
    const gen = job ? job.generated_count : 0;
    const running = job ? RUNNING.has(status) : true;
    const done = job ? DONE.has(status) : false;
    const failed = status === "FAILED";
    const pct = failed ? 100 : done ? 100 : total ? Math.min(95, Math.round((gen / total) * 100)) : 8;

    if (!errMsg) {
      clear(bannerHost);
      if (running) bannerHost.appendChild(el("div", { class: "alert alert-info" },
        el("span", { class: "spin" }, icon("loader")),
        el("div", {}, "Generating questions… this may take several minutes.")));
      else if (done) bannerHost.appendChild(alert("Generation complete! Redirecting to the dashboard…", "success", "checkCircle"));
      else if (failed) bannerHost.appendChild(alert(job.error_message || "Generation failed. Check the backend logs.", "error"));
    }

    clear(metricsHost);
    metricsHost.append(
      metric(status, "Job Status"),
      metric(job && job.skill_name ? job.skill_name.slice(0, 8) : "—", "Skill"),
      metric(jobId.slice(0, 8), "Job ID"),
      metric(job ? job.ssid : "—", "SSID"),
      metric(running ? "Running" : failed ? "Failed" : "Done", "Pipeline",
        failed ? "var(--error)" : done ? "var(--success)" : undefined));

    clear(detailHost).appendChild(card({
      title: "Job Status",
      body: el("div", { class: "flex-col gap-4" },
        el("div", { class: "flex-col gap-2" },
          el("div", { class: "flex justify-between t-sm" },
            el("span", { class: "t-secondary" }, `Generated ${gen} / ${total} rows`),
            el("span", { class: "t-dark" }, `${pct}%`)),
          progressBar(pct)),
        el("div", { class: "grid grid-2" },
          kvBox("Skill Name", job ? job.skill_name : "—"),
          kvBox("Status", status),
          kvBox("SME Email", job ? (job.sme_email || "—") : "—"),
          kvBox("Last Updated", job && job.updated_at ? new Date(job.updated_at).toLocaleTimeString() : "—"))),
    }));

    clear(actionsHost);
    const token = state.get("jobToken");
    actionsHost.appendChild(button("View Requestor Dashboard", {
      variant: "primary",
      onClick: () => navigate(token ? `#/dashboard?job_token=${token}` : "#/dashboard"),
    }));
    if (failed) actionsHost.appendChild(button("Back to Input", { variant: "outline", onClick: () => navigate("#/") }));
  }

  async function tick() {
    if (!document.body.contains(root)) { stop(); return; }
    try {
      if (!started) {
        started = true;
        try { await api.generateQuestions(jobId); }
        catch (e) { if (e.status !== 409) throw e; } // 409 = already generating
      }
      const job = await api.getJob(jobId);
      state.set({ job });
      paint(job);
      if (DONE.has(job.status) || job.status === "FAILED") {
        stop();
        if (DONE.has(job.status) && !navigated) {
          navigated = true;
          const token = job.job_token || state.get("jobToken");
          setTimeout(() => { if (document.body.contains(root)) navigate(token ? `#/dashboard?job_token=${token}` : "#/dashboard"); }, 1600);
        }
      }
    } catch (e) {
      stop();
      paint(state.get("job"), e.message);
    }
  }

  paint(state.get("job"));
  tick();
  interval = setInterval(tick, 3000);
  return root;
}

function kvBox(k, v) {
  return el("div", { class: "kv-box kv" }, el("div", { class: "k" }, k), el("div", { class: "v t-lg" }, v));
}
