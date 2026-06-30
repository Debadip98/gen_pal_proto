// Screen 1 — Request Intake (Input Form)
import { api } from "../api.js";
import { state } from "../state.js";
import {
  el, clear, pageHead, flowStrip, card, badge, button, field, alert, icon, toast,
} from "../components.js";

const ALL_LEVELS = ["ASE", "SE", "SSE", "TL", "AM", "M", "SM"];

// Mirrors backend calculate_complexity_distribution (core/constants.py): the
// fixed 5/6/7/11/11 split for exactly 40, otherwise weighted with the
// remainder assigned Proficient -> Expert -> Advanced -> Intermediate -> Basic.
const COMPLEXITY_WEIGHTS = { Basic: 0.125, Intermediate: 0.15, Advanced: 0.175, Proficient: 0.275, Expert: 0.275 };
const FIXED_40 = { Basic: 5, Intermediate: 6, Advanced: 7, Proficient: 11, Expert: 11 };
const REMAINDER_PRIORITY = ["Proficient", "Expert", "Advanced", "Intermediate", "Basic"];

function complexityDistribution(count) {
  if (count === 40) return { ...FIXED_40 };
  if (count <= 0) return { Basic: 0, Intermediate: 0, Advanced: 0, Proficient: 0, Expert: 0 };
  const dist = {};
  for (const [c, w] of Object.entries(COMPLEXITY_WEIGHTS)) dist[c] = Math.floor(count * w);
  let remainder = count - Object.values(dist).reduce((a, b) => a + b, 0);
  for (const c of REMAINDER_PRIORITY) {
    if (remainder <= 0) break;
    dist[c] += 1; remainder -= 1;
  }
  return dist;
}

export async function render({ navigate }) {
  const form = {
    skill_name: "Microsoft SharePoint Server Development",
    ssid: "80002591",
    requestor_email: "requestor@example.com",
    sme_email: "sme@example.com",
    topics: "SharePoint Server Farm Architecture\nSharePoint Server Object Model\nSharePoint Search Configuration\nSharePoint Security and Permissions",
    urls: "https://learn.microsoft.com/\nhttps://support.microsoft.com/",
    auto_find_docs: false,
    mode: "fixed", // fixed | dynamic
    threshold: 0.85,
    levels: {
      ASE: { enabled: true, count: 40 }, SE: { enabled: true, count: 40 },
      SSE: { enabled: false, count: 40 }, TL: { enabled: false, count: 40 },
      AM: { enabled: false, count: 40 }, M: { enabled: false, count: 40 },
      SM: { enabled: false, count: 40 },
    },
  };
  let loading = false;
  let error = null;

  const root = el("div", { class: "page" });

  function selectedLevels() { return ALL_LEVELS.filter((l) => form.levels[l].enabled); }
  function totalQuestions() { return selectedLevels().reduce((a, l) => a + form.levels[l].count, 0); }

  async function submit() {
    if (!form.skill_name.trim() || selectedLevels().length === 0) {
      error = "Please enter a skill name and select at least one career level.";
      build(); return;
    }
    loading = true; error = null; build();
    try {
      const payload = {
        skill_name: form.skill_name.trim(),
        ssid: form.ssid.trim(),
        requestor_email: form.requestor_email.trim(),
        sme_email: form.sme_email.trim() || null,
        topics: form.topics.split("\n").map((t) => t.trim()).filter(Boolean),
        manual_urls: form.urls.split("\n").map((u) => u.trim()).filter(Boolean),
        generation_mode: form.mode === "fixed" ? "Fixed GenPal Count" : "Dynamic Count",
        career_levels: ALL_LEVELS.map((l) => ({
          career_level: l, enabled: form.levels[l].enabled, question_count: form.levels[l].count,
        })),
        duplicate_threshold: form.threshold,
        auto_find_docs: form.auto_find_docs,
      };
      const job = await api.createJob(payload);
      state.set({ jobId: job.job_id, jobToken: job.job_token, job });
      toast("Job created.", "success");
      navigate(form.auto_find_docs ? "#/docs" : "#/generation");
    } catch (e) {
      error = e.message; loading = false; build();
    }
  }

  function resetForm() {
    form.skill_name = ""; form.ssid = ""; form.requestor_email = ""; form.sme_email = "";
    form.topics = ""; form.urls = ""; form.auto_find_docs = false; form.mode = "fixed";
    form.threshold = 0.85;
    ALL_LEVELS.forEach((l) => { form.levels[l] = { enabled: ["ASE", "SE"].includes(l), count: 40 }; });
    error = null; build();
  }

  function textField(label, key, hint, type = "text") {
    const input = el("input", { class: "input", type, value: form[key],
      oninput: (e) => { form[key] = e.target.value; refreshSummary(); } });
    return field(label, input, hint);
  }
  function textArea(label, key, hint, rows = 4) {
    const ta = el("textarea", { class: "textarea", rows, style: rows >= 4 ? "min-height:7rem" : "" },
      form[key]);
    ta.addEventListener("input", (e) => { form[key] = e.target.value; refreshSummary(); });
    return field(label, ta, hint);
  }

  function levelTable() {
    const head = el("tr", {},
      ...["Enabled", "Career Level", "Question Count", "Complexity Distribution"].map((h) =>
        el("th", {}, h)));
    const body = el("tbody", {});
    ALL_LEVELS.forEach((lv) => {
      const cfg = form.levels[lv];
      const d = complexityDistribution(cfg.count);
      const cb = el("input", { class: "checkbox", type: "checkbox", checked: cfg.enabled,
        onchange: () => { cfg.enabled = !cfg.enabled; build(); } });
      let countCell;
      if (form.mode === "dynamic" && cfg.enabled) {
        countCell = el("input", { class: "input input-num", type: "number", value: cfg.count,
          oninput: (e) => { cfg.count = Math.max(1, parseInt(e.target.value) || 0); refreshSummary(); } });
      } else {
        countCell = el("span", { class: "t-dark" }, String(cfg.count));
      }
      body.appendChild(el("tr", { class: cfg.enabled ? "" : "dim" },
        el("td", {}, cb),
        el("td", {}, badge(lv, cfg.enabled ? "purple" : "outline")),
        el("td", {}, countCell),
        el("td", {}, el("span", { class: "t-xs t-muted" }, `Basic ${d.Basic} · Inter ${d.Intermediate} · Adv ${d.Advanced} · Prof ${d.Proficient} · Expert ${d.Expert}`))));
    });
    return el("div", { class: "tbl-wrap" }, el("table", { class: "tbl" }, el("thead", {}, head), body));
  }

  function modeSeg() {
    return el("div", { class: "seg" },
      el("button", { class: form.mode === "fixed" ? "active" : "", onClick: () => { form.mode = "fixed"; build(); } }, "Fixed GenPal Count"),
      el("button", { class: form.mode === "dynamic" ? "active" : "", onClick: () => { form.mode = "dynamic"; build(); } }, "Dynamic Count"));
  }

  let summaryHost;
  function summaryCard() {
    const sl = selectedLevels();
    const body = el("div", { class: "flex-col gap-3" },
      kv("Skill Name", form.skill_name || "—"),
      kv("Skill ID / SSID", form.ssid || "—"),
      kv("Requestor Email", form.requestor_email || "—"),
      kv("SME Email", form.sme_email || "—"),
      el("div", { class: "kv" },
        el("div", { class: "k" }, "Selected Career Levels"),
        el("div", { class: "flex flex-wrap gap-1 mt-1" },
          sl.length ? sl.map((l) => badge(l, "gray")) : el("span", { class: "t-xs t-muted" }, "None selected"))),
      kv("Total Expected Questions", String(totalQuestions())),
      el("div", { class: "border-t pt-3 kv" },
        el("div", { class: "k" }, "Output File Name"),
        el("div", { class: "v break" }, form.skill_name && form.ssid ? `${form.skill_name}-${form.ssid}.xlsx` : "—")),
      el("div", { class: "kv-box flex-col gap-2" },
        kvRow("Sheet name:", "Sheet1"),
        kvRow("Columns:", "11"),
        kvRow("Threshold:", form.threshold.toFixed(2))),
      form.auto_find_docs ? alert("Auto-documentation discovery enabled. You will be directed to the Docs Discovery screen first.", "info") : null);
    return card({ title: "Expected Output Summary", body });
  }
  function refreshSummary() {
    if (!summaryHost) return;
    clear(summaryHost).appendChild(summaryCard());
  }

  function build() {
    clear(root);
    root.appendChild(pageHead("GenPal Question Bank Factory",
      "AI-assisted question bank generation with SME review and GenPal-ready Excel export."));
    root.appendChild(flowStrip(0));
    if (error) root.appendChild(alert(error, "error"));

    const autoCard = el("div", { class: "checkbox-card" },
      el("input", { class: "checkbox", type: "checkbox", checked: form.auto_find_docs,
        onchange: () => { form.auto_find_docs = !form.auto_find_docs; build(); } }),
      el("div", {},
        el("label", { class: "lbl" }, "Auto-find latest documentation from web based on Skill Name"),
        el("div", { class: "hint mt-1" }, "The system will search official/latest docs and suggest additional references.")));

    const threshValue = el("span", { class: "t-sm t-dark" }, form.threshold.toFixed(2));
    const threshRange = el("input", { type: "range", min: "0.5", max: "1", step: "0.05", value: String(form.threshold) });
    threshRange.addEventListener("input", (e) => {
      form.threshold = parseFloat(e.target.value);
      threshValue.textContent = form.threshold.toFixed(2);
      refreshSummary();
    });
    const thresholdRow = el("div", { class: "field" },
      el("div", { class: "flex items-center justify-between" },
        el("label", { class: "lbl" }, "Duplicate Similarity Threshold"), threshValue),
      threshRange,
      el("div", { class: "hint" }, "Questions above this similarity score are flagged for duplicate review."));

    const formCard = card({
      title: "Input Form",
      desc: "Enter the required details for question bank generation.",
      body: el("div", { class: "flex-col gap-4" },
        el("div", { class: "grid grid-2" }, textField("Skill Name", "skill_name", "Enter the skill name exactly as it should appear in Excel."), textField("Skill ID / SSID", "ssid", "This value will be repeated in every Excel row.")),
        el("div", { class: "grid grid-2" }, textField("Requestor Email", "requestor_email", "Notifications will be sent to this email after SME actions.", "email"), textField("SME Email ID", "sme_email", "The SME review link will be sent to this email.", "email")),
        textArea("Topic List", "topics", "Paste one topic per line.", 5),
        textArea("Reference URL List", "urls", "Paste one reference URL per line.", 3),
        autoCard,
        el("div", { class: "field" }, el("label", { class: "lbl" }, "Generation Mode"), modeSeg(),
          el("div", { class: "hint" }, form.mode === "fixed" ? "Fixed GenPal Count: 40 questions per selected career level." : "Dynamic Count: Enter a custom question count per career level.")),
        el("div", { class: "field" }, el("label", { class: "lbl" }, "Career Level Configuration"), levelTable()),
        thresholdRow,
        el("div", { class: "flex gap-3 pt-3" },
          button(loading ? "Creating Job…" : "Generate Question Bank", { variant: "primary", block: true, disabled: loading, iconName: loading ? "loader" : undefined, onClick: submit }),
          button("Reset Form", { variant: "outline", iconName: "reset", disabled: loading, onClick: resetForm }))),
    });

    summaryHost = el("div", {}, summaryCard());
    root.appendChild(el("div", { class: "grid col-2-1" },
      el("div", { class: "flex-col gap-4" }, formCard),
      summaryHost));
  }

  build();
  return root;
}

function kv(k, v) {
  return el("div", { class: "kv" }, el("div", { class: "k" }, k), el("div", { class: "v break" }, v));
}
function kvRow(k, v) {
  return el("div", { class: "kv-row" }, el("span", { class: "k" }, k), el("span", { class: "v" }, v));
}
