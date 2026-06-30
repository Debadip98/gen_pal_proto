// Screen 4 — Requestor Dashboard
import { api } from "../api.js";
import { state } from "../state.js";
import {
  el, clear, pageHead, card, badge, button, alert, icon, progressBar, metric, toast,
} from "../components.js";
import { questionStatusBadge } from "./_shared.js";

export async function render({ navigate, query }) {
  const token = query.job_token || state.get("jobToken");
  const root = el("div", { class: "page" });
  root.appendChild(pageHead("Requestor Dashboard", "Monitor SME review progress, notifications, and download options."));

  if (!token) {
    root.appendChild(alert("No active job. Start from the Input Form.", "warning"));
    root.appendChild(button("Back to Input", { variant: "outline", onClick: () => navigate("#/") }));
    return root;
  }

  let dash, questions = [], notifResp = { notifications: [], unread_count: 0 };
  try {
    dash = await api.getDashboard(token);
    state.set({ jobToken: token, jobId: dash.job_id, dashboard: dash });
  } catch (e) {
    root.appendChild(alert(e.message, "error"));
    root.appendChild(button("Back to Input", { variant: "outline", onClick: () => navigate("#/") }));
    return root;
  }
  try { questions = await api.getQuestions(dash.job_id); } catch { /* best effort */ }
  try { notifResp = await api.getNotifications(token); } catch { /* best effort */ }

  const total = dash.total_questions;
  const accepted = dash.accepted_count, rejected = dash.rejected_count, pending = dash.pending_count;
  const dupWarn = questions.filter((q) => q.duplicate_warning).length;
  let notifs = notifResp.notifications || [];
  let unread = notifResp.unread_count || 0;

  // Metric strip (10 compact cards)
  const metrics = [
    ["Skill", (dash.skill_name || "—").slice(0, 10)],
    ["SSID", dash.ssid || "—"],
    ["Total Q", String(total)],
    ["Accepted", String(accepted), "var(--success)"],
    ["Rejected", String(rejected), "var(--error)"],
    ["Pending", String(pending)],
    ["Dup Warns", String(dupWarn), "var(--warning)"],
    ["Job ID", dash.job_id.slice(0, 6)],
    ["Notifs", String(notifs.length)],
    ["Unread", String(unread), unread > 0 ? "var(--genpal-purple)" : undefined],
  ];
  const mGrid = el("div", { class: "grid grid-5" });
  metrics.forEach(([l, v, c]) => mGrid.appendChild(metric(v, l, c)));
  root.appendChild(mGrid);

  // Progress
  root.appendChild(card({
    body: el("div", { class: "flex-col gap-2" },
      el("div", { class: "flex justify-between t-sm" },
        el("span", { class: "t-secondary" }, "SME Review Progress"),
        el("span", { class: "t-dark" }, `Accepted ${accepted} / ${total}`)),
      progressBar(total ? (accepted / total) * 100 : 0),
      el("div", { class: "t-xs t-muted" }, `${pending} questions still pending review.`)),
  }));

  // Notifications + question table
  const notifBody = el("div", { class: "flex-col gap-2" });
  function renderNotifs() {
    clear(notifBody);
    if (!notifs.length) { notifBody.appendChild(el("p", { class: "t-xs t-muted" }, "No notifications yet.")); return; }
    notifs.forEach((n) => {
      notifBody.appendChild(el("div", {
        class: "kv-box",
        style: `padding:0.65rem;${!n.is_read ? "border:1px solid rgba(161,0,255,0.35);background:rgba(161,0,255,0.05)" : ""}`,
      },
        el("div", { class: "flex items-start justify-between gap-2" },
          el("div", { class: "flex-1" },
            el("p", { class: "t-xs t-dark" }, n.message),
            el("p", { class: "t-xs t-muted mt-1" }, new Date(n.created_at).toLocaleTimeString())),
          !n.is_read ? el("span", { style: "width:8px;height:8px;border-radius:50%;background:var(--genpal-purple);margin-top:4px;flex-shrink:0" }) : null)));
    });
  }
  renderNotifs();
  const notifCard = card({
    title: "SME Review Notifications",
    headRight: button("Mark All Read", { variant: "ghost", sm: true, onClick: async () => {
      try { await api.markAllNotificationsRead(token); notifs = notifs.map((n) => ({ ...n, is_read: true })); unread = 0; renderNotifs(); toast("All marked read.", "success"); }
      catch (e) { toast(e.message, "error"); }
    } }),
    body: notifBody,
  });

  const qRows = el("tbody", {});
  questions.slice(0, 20).forEach((q) => {
    qRows.appendChild(el("tr", {},
      el("td", { class: "t-xs" }, String(q.title)),
      el("td", { style: "max-width:120px" }, el("p", { class: "t-xs line-2" }, q.topic || "—")),
      el("td", {}, badge(q.career_level, "outline")),
      el("td", { class: "t-xs" }, q.complexity),
      el("td", {}, questionStatusBadge(q.status)),
      el("td", {}, q.duplicate_warning ? icon("alert", "ico") : el("span", { class: "t-xs t-muted" }, "—"))));
  });
  const qTable = el("div", { class: "tbl-wrap" },
    el("table", { class: "tbl" },
      el("thead", {}, el("tr", {}, ...["title", "topic", "career_level", "complexity", "status", "dup"].map((h) => el("th", {}, h)))),
      qRows));
  const qCard = card({ title: "Question Status Table", body: questions.length ? qTable : el("div", { class: "empty-state" }, "No questions yet.") });

  root.appendChild(el("div", { class: "grid", style: "grid-template-columns:1fr 2fr" }, notifCard, qCard));

  // Download cards
  let busy = false;
  const dl = async (type) => {
    if (busy) return; busy = true;
    try { api.exportExcel(dash.job_id, type); toast(`${type === "approved" ? "Approved" : "Draft"} Excel download started.`, "success"); }
    finally { setTimeout(() => (busy = false), 800); }
  };
  const draftCard = el("div", { class: "card", style: "border-width:2px" },
    el("div", { class: "card-body flex-col gap-3" },
      el("div", { class: "card-title flex items-center gap-2" }, icon("download"), "Download Current Draft Excel"),
      el("p", { class: "t-xs t-secondary" }, "Always available once generated rows exist. May include questions not fully accepted by SME."),
      badge("Some questions may still be pending SME review.", "outline-amber", "alert"),
      button("Download Draft Excel", { variant: "outline", block: true, iconName: "download", disabled: !dash.draft_download_ready, onClick: () => dl("draft") })));
  const apprCard = el("div", { class: "card", style: "border:2px solid var(--success)" },
    el("div", { class: "card-body flex-col gap-3" },
      el("div", { class: "card-title flex items-center gap-2" }, icon("download"), "Download Approved Excel"),
      el("p", { class: "t-xs t-secondary" }, "Available after all questions are accepted or final override is confirmed."),
      dash.approved_download_ready ? badge("SME Review Complete", "success", "checkCircle") : badge("Pending full approval", "gray"),
      button("Download Approved Excel", { variant: "success", block: true, iconName: "download", disabled: !dash.approved_download_ready, onClick: () => dl("approved") })));
  root.appendChild(el("div", { class: "grid grid-2" }, draftCard, apprCard));

  root.appendChild(el("div", { class: "flex justify-between" },
    button("Back to Generation", { variant: "outline", onClick: () => navigate("#/generation") }),
    button("Send to SME Review", { variant: "primary", onClick: () => navigate("#/send-review") })));

  return root;
}
