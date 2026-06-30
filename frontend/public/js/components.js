// Shared UI: DOM helpers, icons, layout (header + sidebar), and reusable
// building blocks (card, badge, table, button, alert, flow stepper, toast,
// modal, drawer). Page modules compose these.

import { state } from "./state.js";

/* --- el(): minimal hyperscript ------------------------------------------- */
export function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v == null || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k === "style") node.setAttribute("style", v);
    else if (k.startsWith("on") && typeof v === "function") {
      node.addEventListener(k.slice(2).toLowerCase(), v);
    } else if (k === "value") node.value = v;
    else if (k === "checked" || k === "disabled") node[k] = !!v;
    else node.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    node.appendChild(typeof c === "string" || typeof c === "number" ? document.createTextNode(String(c)) : c);
  }
  return node;
}

export function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
  return node;
}

/* --- Icons (lucide-style inline SVG) ------------------------------------- */
const ICONS = {
  fileInput: '<path d="M4 22h14a2 2 0 0 0 2-2V7l-5-5H6a2 2 0 0 0-2 2v4"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M2 15h10"/><path d="m9 18 3-3-3-3"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  loader: '<line x1="12" x2="12" y1="2" y2="6"/><line x1="12" x2="12" y1="18" y2="22"/><line x1="4.93" x2="7.76" y1="4.93" y2="7.76"/><line x1="16.24" x2="19.07" y1="16.24" y2="19.07"/><line x1="2" x2="6" y1="12" y2="12"/><line x1="18" x2="22" y1="12" y2="12"/><line x1="4.93" x2="7.76" y1="19.07" y2="16.24"/><line x1="16.24" x2="19.07" y1="7.76" y2="4.93"/>',
  dashboard: '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
  send: '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
  clipboard: '<rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>',
  message: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
  refresh: '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
  gitBranch: '<line x1="6" x2="6" y1="3" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
  dollar: '<line x1="12" x2="12" y1="2" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
  settings: '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
  user: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  check: '<polyline points="20 6 9 17 4 12"/>',
  checkCircle: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  alertCircle: '<circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>',
  arrowRight: '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
  copy: '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
  clock: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  lock: '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  external: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  reset: '<path d="M3 2v6h6"/><path d="M3 13a9 9 0 1 0 3-7.7L3 8"/>',
  mail: '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
};

export function icon(name, cls = "ico") {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${cls}">${ICONS[name] || ""}</svg>`;
  const wrap = document.createElement("span");
  wrap.style.display = "inline-flex";
  wrap.innerHTML = svg;
  return wrap.firstChild;
}

/* --- Primitive components ------------------------------------------------ */
export function badge(text, variant = "gray", iconName) {
  return el("span", { class: `badge badge-${variant}` }, iconName ? icon(iconName, "ico") : null, text);
}

export function button(label, { variant = "primary", onClick, iconName, sm, block, disabled, type } = {}) {
  const cls = ["btn", `btn-${variant}`, sm ? "btn-sm" : "", block ? "btn-block" : ""].filter(Boolean).join(" ");
  return el("button", { class: cls, onClick, disabled, type: type || "button" }, iconName ? icon(iconName) : null, label);
}

export function card({ title, desc, body, headRight } = {}) {
  const head = title
    ? el("div", { class: "card-head" },
        el("div", { class: "flex items-center justify-between" },
          el("div", {},
            el("div", { class: "card-title" }, title),
            desc ? el("div", { class: "card-desc" }, desc) : null),
          headRight || null))
    : null;
  return el("div", { class: "card" }, head, el("div", { class: "card-body" }, body));
}

export function metric(value, label, color) {
  return el("div", { class: "metric" },
    el("div", { class: "m-value", style: color ? `color:${color}` : "" }, String(value)),
    el("div", { class: "m-label" }, label));
}

export function alert(message, variant = "info", iconName) {
  const map = { info: "alertCircle", success: "checkCircle", warning: "alert", error: "alertCircle" };
  return el("div", { class: `alert alert-${variant}` },
    icon(iconName || map[variant] || "alertCircle"),
    el("div", {}, message));
}

export function field(labelText, control, hint) {
  return el("div", { class: "field" },
    labelText ? el("label", {}, labelText) : null,
    control,
    hint ? el("div", { class: "hint" }, hint) : null);
}

export function progressBar(pct) {
  return el("div", { class: "progress" }, el("span", { style: `width:${Math.max(0, Math.min(100, pct))}%` }));
}

/* --- Flow stepper -------------------------------------------------------- */
export function flowStrip(activeIdx, steps = ["Input", "Generate", "Validate", "SME Review", "Export"]) {
  const row = el("div", { class: "flow-strip" });
  steps.forEach((label, i) => {
    const stDot = i < activeIdx ? "done" : i === activeIdx ? "active" : "";
    const step = el("div", { class: "flow-step" },
      el("div", { class: `flow-dot ${stDot}` }, i < activeIdx ? icon("check", "ico") : String(i + 1)),
      el("div", { class: `flow-label ${stDot}` }, label));
    row.appendChild(step);
    if (i < steps.length - 1) row.appendChild(el("span", { class: "flow-arrow" }, "›"));
  });
  return row;
}

/* --- Table --------------------------------------------------------------- */
// columns: [{ head, render(row) -> node|string, width }]
export function table(columns, rows, { rowClass, onRowClick } = {}) {
  const thead = el("thead", {}, el("tr", {}, ...columns.map((c) => el("th", { style: c.width ? `width:${c.width}` : "" }, c.head))));
  const tbody = el("tbody", {});
  rows.forEach((r) => {
    const tr = el("tr", {
      class: [rowClass ? rowClass(r) : "", onRowClick ? "clickable" : ""].filter(Boolean).join(" "),
      onClick: onRowClick ? () => onRowClick(r) : undefined,
    }, ...columns.map((c) => {
      const v = c.render(r);
      return el("td", {}, typeof v === "string" || typeof v === "number" ? String(v) : v);
    }));
    tbody.appendChild(tr);
  });
  return el("div", { class: "tbl-wrap" }, el("table", { class: "tbl" }, thead, tbody));
}

/* --- Toast --------------------------------------------------------------- */
export function toast(message, variant = "info", ms = 3200) {
  const root = document.getElementById("toast-root");
  const t = el("div", { class: `toast ${variant}` }, message);
  root.appendChild(t);
  setTimeout(() => {
    t.style.transition = "opacity 0.25s";
    t.style.opacity = "0";
    setTimeout(() => t.remove(), 250);
  }, ms);
}

/* --- Overlay: modal & drawer --------------------------------------------- */
function mountOverlay(node, { drawer = false } = {}) {
  const root = document.getElementById("overlay-root");
  const overlay = el("div", { class: `overlay ${drawer ? "drawer-overlay" : ""}` }, node);
  overlay.addEventListener("mousedown", (e) => { if (e.target === overlay) close(); });
  function close() { overlay.remove(); }
  root.appendChild(overlay);
  return close;
}

export function modal({ title, body, footer }) {
  let close = () => {};
  const head = el("div", { class: "modal-head" },
    el("div", { class: "card-title" }, title || ""),
    el("button", { class: "icon-btn", onClick: () => close() }, icon("x")));
  const m = el("div", { class: "modal" }, head, el("div", { class: "modal-body" }, body),
    footer ? el("div", { class: "modal-foot" }, ...(Array.isArray(footer) ? footer : [footer])) : null);
  close = mountOverlay(m);
  return close;
}

export function drawer({ title, body, footer }) {
  let close = () => {};
  const head = el("div", { class: "modal-head" },
    el("div", { class: "card-title" }, title || ""),
    el("button", { class: "icon-btn", onClick: () => close() }, icon("x")));
  const d = el("div", { class: "drawer" }, head, el("div", { class: "modal-body" }, body),
    footer ? el("div", { class: "modal-foot" }, ...(Array.isArray(footer) ? footer : [footer])) : null);
  close = mountOverlay(d, { drawer: true });
  return close;
}

/* --- Page header block --------------------------------------------------- */
export function pageHead(title, sub) {
  return el("div", { class: "page-head" },
    el("h2", { class: "page-title" }, title),
    sub ? el("p", { class: "page-sub" }, sub) : null);
}

/* --- App header ---------------------------------------------------------- */
function appHeader(navigate) {
  const userType = state.get("userType");
  const online = state.get("backendOnline");
  const mock = state.get("mockMode");
  // Offline is its own state — never let an unreachable backend masquerade as
  // "Mock Mode" (that misled us into thinking generation wasn't calling OpenAI).
  const statusBadge = online === false
    ? badge("Backend offline", "error", "alertCircle")
    : badge(mock ? "Mock Mode" : "Live API", mock ? "outline-purple" : "success");
  return el("header", { class: "gp-header" },
    el("div", { class: "gp-header-left" },
      el("div", { class: "gp-logo" }, "GQ"),
      el("h1", { class: "gp-header-title" }, "GenPal Question Bank Factory")),
    el("div", { class: "gp-header-right" },
      statusBadge,
      el("div", { class: "role-toggle" },
        el("button", {
          class: userType === "requestor" ? "active-req" : "",
          onClick: () => { state.set({ userType: "requestor" }); navigate("#/"); },
        }, "Requestor"),
        el("button", {
          class: userType === "sme" ? "active-sme" : "",
          onClick: () => { state.set({ userType: "sme" }); navigate("#/sme-review"); },
        }, "SME")),
      el("button", { class: "icon-btn" }, icon("settings")),
      el("button", { class: "icon-btn" }, icon("user"))));
}

/* --- App sidebar --------------------------------------------------------- */
const NAV_GROUPS = [
  { label: "Requestor", roles: ["requestor"], items: [
    { hash: "#/", label: "Input", icon: "fileInput" },
    { hash: "#/docs", label: "Docs Discovery", icon: "search" },
    { hash: "#/generation", label: "Generation", icon: "loader" },
    { hash: "#/dashboard", label: "Requestor Dashboard", icon: "dashboard" },
    { hash: "#/send-review", label: "Send to SME", icon: "send" },
  ]},
  { label: "SME", roles: ["sme"], items: [
    { hash: "#/review", label: "SME Review", icon: "clipboard" },
    { hash: "#/sme-question", label: "Question Review", icon: "message" },
    { hash: "#/regenerate", label: "Rework", icon: "refresh" },
    { hash: "#/version-compare", label: "Version Compare", icon: "gitBranch" },
    { hash: "#/doc-check", label: "Doc Alignment", icon: "search" },
    { hash: "#/review-complete", label: "Review Complete", icon: "clipboard" },
  ]},
  { label: "Output", roles: ["requestor"], items: [
    { hash: "#/export", label: "Export", icon: "download" },
    { hash: "#/cost", label: "Cost Summary", icon: "dollar" },
    { hash: "#/flow", label: "Business Flow", icon: "gitBranch" },
  ]},
];

function appSidebar(navigate, currentPath) {
  const userType = state.get("userType");
  const groups = NAV_GROUPS.filter((g) => g.roles.includes(userType));
  const roleCls = userType === "sme" ? "sme" : "req";
  const nav = el("nav", { class: "sb-nav" });
  groups.forEach((g) => {
    const block = el("div", {}, el("span", { class: "sb-group-label" }, g.label));
    g.items.forEach((it) => {
      const active = currentPath === it.hash;
      block.appendChild(el("button", {
        class: `sb-item ${active ? "active " + roleCls : ""}`,
        onClick: () => navigate(it.hash),
      }, icon(it.icon, "ico"), el("span", {}, it.label)));
    });
    nav.appendChild(block);
  });
  return el("aside", { class: "gp-sidebar" },
    el("div", { class: `sb-interface ${userType === "sme" ? "sme" : ""}` },
      el("p", {}, userType === "sme" ? "SME Interface" : "Requestor Interface")),
    nav);
}

/* --- Layout: render header + sidebar + page content ---------------------- */
// pageNode: the content element. currentPath: hash like "#/docs".
export function layout(pageNode, navigate, currentPath) {
  const main = el("main", { class: "app-main" },
    el("div", { class: "app-content" }, pageNode),
    el("footer", { class: "app-footer" },
      el("p", {}, "Prototype design. Official brand assets and templates should be applied only from approved internal sources.")));
  return el("div", { class: "app-shell" },
    appHeader(navigate),
    el("div", { class: "app-body" }, appSidebar(navigate, currentPath), main));
}
