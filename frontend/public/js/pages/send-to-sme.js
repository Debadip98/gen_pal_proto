// Screen 5 — Send to SME Review
import { api } from "../api.js";
import { state } from "../state.js";
import {
  el, clear, pageHead, card, badge, button, alert, icon, toast,
} from "../components.js";

export async function render({ navigate }) {
  const jobId = state.get("jobId");
  const root = el("div", { class: "page" });
  root.appendChild(pageHead("Send to SME Review", "Send the secure review link to the SME for question-by-question review."));

  const bannerHost = el("div", {});
  root.appendChild(bannerHost);

  let reviewLink = null, reviewToken = null, sent = false, loading = false;
  const smeEmail = (state.get("job") && state.get("job").sme_email) || "sme@example.com";

  const linkHost = el("div", {});
  const emailHost = el("div", {});
  const actionsHost = el("div", {});
  root.append(linkHost, emailHost, actionsHost);

  function displayLink() { return reviewLink || `(link appears here after sending)`; }

  function renderLinkCard() {
    clear(linkHost).appendChild(card({
      title: "Review Link",
      body: el("div", { class: "flex-col gap-3" },
        el("div", { class: "flex items-center gap-2 kv-box", style: "padding:0.75rem 1rem" },
          el("code", { class: "flex-1 t-xs mono t-info break" }, displayLink()),
          button("", { variant: "ghost", sm: true, iconName: "copy", disabled: !reviewLink, onClick: copyLink })),
        el("div", { class: "t-xs t-muted" }, "This link grants secure SME access to the review workspace. It is valid for 72 hours.")),
    }));
  }

  function renderEmailCard() {
    clear(emailHost).appendChild(card({
      title: "Email Preview",
      headRight: null,
      body: el("div", { class: "kv-box flex-col gap-3", style: "padding:1.25rem" },
        el("div", { class: "flex-col gap-1" },
          el("div", { class: "flex gap-2 t-xs" }, el("span", { class: "t-muted", style: "width:54px" }, "To:"), el("span", { class: "t-dark" }, smeEmail)),
          el("div", { class: "flex gap-2 t-xs" }, el("span", { class: "t-muted", style: "width:54px" }, "Subject:"), el("span", { class: "t-dark" }, "GenPal Question Bank Review Required"))),
        el("div", { class: "border-t pt-3 flex-col gap-2 t-sm t-dark" },
          el("p", {}, "Dear SME,"),
          el("p", {}, "A GenPal question bank has been generated and requires your expert review."),
          el("p", {}, "Please use the secure review link below to access the SME Review Workspace:"),
          el("p", { class: "t-xs mono t-info break", style: "background:#fff;border:1px solid var(--border);border-radius:6px;padding:0.5rem 0.75rem" }, displayLink()),
          el("p", { class: "t-xs t-muted" }, "This link is valid for 72 hours."))),
    }));
  }

  async function copyLink() {
    if (!reviewLink) return;
    try { await navigator.clipboard.writeText(reviewLink); toast("Review link copied.", "success"); }
    catch { toast("Copy failed — select the link manually.", "error"); }
  }

  async function send() {
    if (!jobId) { clear(bannerHost).appendChild(alert("No active job found. Generate a question bank first.", "error")); return; }
    loading = true; renderActions();
    try {
      const res = await api.sendSmeReview(jobId);
      reviewToken = res.review_token;
      reviewLink = res.review_link;
      state.set({ reviewToken });
      sent = true; loading = false;
      clear(bannerHost).appendChild(alert(
        (res.email_sent ? "SME review email sent successfully. " : "Email not configured — share the link below. ") + "Redirecting to dashboard…",
        "success", "checkCircle"));
      renderLinkCard(); renderEmailCard(); renderActions();
      const token = state.get("jobToken");
      setTimeout(() => { if (document.body.contains(root)) navigate(token ? `#/dashboard?job_token=${token}` : "#/dashboard"); }, 3000);
    } catch (e) {
      loading = false;
      clear(bannerHost).appendChild(alert(e.message, "error"));
      renderActions();
    }
  }

  function renderActions() {
    clear(actionsHost).appendChild(el("div", { class: "flex justify-between" },
      button("Back to Dashboard", { variant: "outline", onClick: () => navigate("#/dashboard") }),
      el("div", { class: "flex gap-3" },
        button("Copy Review Link", { variant: "outline", iconName: "copy", disabled: !reviewLink, onClick: copyLink }),
        button(loading ? "Sending…" : "Send SME Review Email", { variant: "primary", iconName: loading ? "loader" : "send", disabled: loading || sent, onClick: send }))));
  }

  renderLinkCard(); renderEmailCard(); renderActions();
  return root;
}
