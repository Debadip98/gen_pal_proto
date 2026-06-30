// Screen 10 — Documentation Context & Alignment
import { api } from "../api.js";
import { state } from "../state.js";
import {
  el, clear, pageHead, card, badge, button, alert, icon,
} from "../components.js";

function domainOf(url) {
  try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return url || "—"; }
}
function alignmentBadge(a) {
  if (a === "ALIGNED") return badge("ALIGNED", "success");
  if (a === "PARTIALLY_ALIGNED") return badge("PARTIALLY ALIGNED", "outline-amber");
  if (a === "NOT_ALIGNED") return badge("NOT ALIGNED", "outline-red");
  return badge("INSUFFICIENT CONTEXT", "outline");
}

export async function render({ navigate }) {
  const token = state.get("reviewToken");
  const root = el("div", { class: "page" });
  root.appendChild(pageHead("Documentation Context and Alignment", "Review how questions are checked against reference documentation."));

  if (!token) {
    root.appendChild(alert("Open the SME review workspace from the secure link first.", "info"));
    root.appendChild(button("Go to Review Queue", { variant: "primary", onClick: () => navigate("#/review") }));
    return root;
  }

  let session, job, q;
  try {
    session = await api.getReviewSession(token);
    q = (session.questions || []).find((x) => x.question_id === state.get("selectedQuestionId")) || (session.questions || [])[0];
    job = state.get("job") || await api.getJob(session.job_id);
    state.set({ job });
  } catch (e) { root.appendChild(alert(e.message, "error")); return root; }

  const manual = (job && job.manual_urls) || [];
  const selected = (job && job.selected_urls) || [];

  // Tabs: Manual URLs / Selected (Used) Docs
  const tabs = ["Manual URLs", "Selected Docs", "Used Context"];
  let active = "Manual URLs";
  const seg = el("div", { class: "seg" });
  const listHost = el("div", {});

  function urlsFor(tab) {
    if (tab === "Manual URLs") return manual;
    if (tab === "Selected Docs") return selected;
    return [...new Set([...selected, ...manual])];
  }
  function renderSeg() {
    clear(seg);
    tabs.forEach((t) => seg.appendChild(el("button", { class: active === t ? "active" : "", onClick: () => { active = t; renderSeg(); renderList(); } }, t)));
  }
  function renderList() {
    const urls = urlsFor(active);
    clear(listHost);
    if (!urls.length) { listHost.appendChild(el("div", { class: "empty-state" }, "No documents in this category.")); return; }
    const body = el("tbody", {});
    urls.forEach((url) => {
      body.appendChild(el("tr", {},
        el("td", {}, el("div", { class: "flex items-center gap-1" }, icon("external", "ico"), el("span", { class: "t-xs t-dark break" }, url))),
        el("td", {}, el("span", { class: "t-xs t-secondary" }, domainOf(url))),
        el("td", {}, badge("Reference", "outline")),
        el("td", {}, url ? el("a", { href: url, target: "_blank", rel: "noopener", class: "t-xs" }, "Open") : "—")));
    });
    listHost.appendChild(el("div", { class: "tbl-wrap" },
      el("table", { class: "tbl" },
        el("thead", {}, el("tr", {}, ...["Source URL", "Domain", "Type", "Link"].map((h) => el("th", {}, h)))),
        body)));
  }
  renderSeg(); renderList();
  root.appendChild(seg);
  root.appendChild(card({ title: "Documentation Sources", body: listHost }));

  // Selected question alignment
  const status = q ? q.doc_alignment_status : null;
  const alignNote = {
    ALIGNED: ["The question is aligned with the selected reference documentation.", "success"],
    PARTIALLY_ALIGNED: ["The question is partially aligned. Some claims may need a documentation check.", "warning"],
    NOT_ALIGNED: ["The question does not align with the selected documentation. Consider regenerating.", "error"],
  }[status] || ["Documentation alignment has not been evaluated for this question yet.", "info"];

  root.appendChild(el("div", { class: "card", style: "border:2px solid var(--genpal-purple)" },
    el("div", { class: "card-head" }, el("div", { class: "card-title" }, "Question Documentation Alignment")),
    el("div", { class: "card-body flex-col gap-4" },
      el("div", {}, el("p", { class: "t-xs t-muted" }, "Current Question"), el("p", { class: "t-sm t-dark mt-1" }, q ? q.question : "—")),
      el("div", { class: "grid grid-2" },
        el("div", {}, el("p", { class: "t-xs t-muted" }, "Reference Source Used"), el("p", { class: "t-sm t-info mt-1 break" }, q && q.reference_url ? q.reference_url : "—")),
        el("div", {}, el("p", { class: "t-xs t-muted" }, "Alignment Status"), el("div", { class: "mt-1" }, alignmentBadge(status))),
      ),
      alert(alignNote[0], alignNote[1]))));

  root.appendChild(el("div", { class: "flex justify-between" },
    button("Back to Question", { variant: "outline", onClick: () => navigate("#/sme-question") }),
    button("Back to Rework", { variant: "primary", onClick: () => navigate("#/regenerate") })));

  return root;
}
