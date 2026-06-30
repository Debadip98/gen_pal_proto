// Hash-based router. Parses "#/path?query", resolves the page module, sets
// role/token context, and renders the layout + page into #app.
//
//   #/                      Request Intake (requestor)
//   #/docs                  Documentation Discovery
//   #/generation            Generation Progress
//   #/dashboard?job_token=  Requestor Dashboard
//   #/send-review           Send to SME
//   #/review?review_token=  SME Review Workspace
//   #/sme-question          SME Question Review Detail
//   #/regenerate            Regenerate Selected Question
//   #/version-compare       Question Version Comparison
//   #/doc-check             Documentation Context & Alignment
//   #/review-complete       SME Final Review Complete
//   #/export                Export & Download Center
//   #/cost                  Cost & Traceability Summary
//   #/flow                  Business Flow Overview

import { state } from "./state.js";
import { layout, el, icon } from "./components.js";
import { api } from "./api.js";

import * as requestIntake from "./pages/request-intake.js";
import * as docsDiscovery from "./pages/docs-discovery.js";
import * as generationProgress from "./pages/generation-progress.js";
import * as requestorDashboard from "./pages/requestor-dashboard.js";
import * as sendToSme from "./pages/send-to-sme.js";
import * as smeReview from "./pages/sme-review.js";
import * as smeQuestion from "./pages/sme-question.js";
import * as questionRework from "./pages/question-rework.js";
import * as versionComparison from "./pages/version-comparison.js";
import * as docAlignment from "./pages/doc-alignment.js";
import * as smeReviewComplete from "./pages/sme-review-complete.js";
import * as exportCenter from "./pages/export-center.js";
import * as costTraceability from "./pages/cost-traceability.js";
import * as businessFlow from "./pages/business-flow.js";

// Map canonical hash path -> { module, role }
const ROUTES = {
  "#/": { mod: requestIntake, role: "requestor" },
  "#/docs": { mod: docsDiscovery, role: "requestor" },
  "#/generation": { mod: generationProgress, role: "requestor" },
  "#/dashboard": { mod: requestorDashboard, role: "requestor" },
  "#/send-review": { mod: sendToSme, role: "requestor" },
  "#/review": { mod: smeReview, role: "sme" },
  "#/sme-question": { mod: smeQuestion, role: "sme" },
  "#/regenerate": { mod: questionRework, role: "sme" },
  "#/version-compare": { mod: versionComparison, role: "sme" },
  "#/doc-check": { mod: docAlignment, role: "sme" },
  "#/review-complete": { mod: smeReviewComplete, role: "sme" },
  "#/export": { mod: exportCenter, role: "requestor" },
  "#/cost": { mod: costTraceability, role: "requestor" },
  "#/flow": { mod: businessFlow, role: "requestor" },
};

// Aliases -> canonical hash
const ALIASES = {
  "": "#/",
  "#": "#/",
  "#/request-intake": "#/",
  "#/progress": "#/generation",
  "#/generation-progress": "#/generation",
  "#/requestor-dashboard": "#/dashboard",
  "#/send-to-sme": "#/send-review",
  "#/sme-review": "#/review",
  "#/question-review": "#/sme-question",
  "#/question-rework": "#/regenerate",
  "#/doc-alignment": "#/doc-check",
  "#/export-center": "#/export",
  "#/cost-traceability": "#/cost",
  "#/business-flow": "#/flow",
};

function parseHash() {
  const raw = window.location.hash || "#/";
  const [pathPart, queryPart] = raw.split("?");
  let path = pathPart || "#/";
  if (ALIASES[path] !== undefined) path = ALIASES[path];
  const query = {};
  if (queryPart) {
    new URLSearchParams(queryPart).forEach((v, k) => (query[k] = v));
  }
  return { path, query };
}

export function navigate(hash) {
  if (window.location.hash === hash) {
    render(); // force re-render if navigating to same hash
  } else {
    window.location.hash = hash;
  }
}

function loadingNode() {
  return el("div", { class: "page" },
    el("div", { class: "flex items-center gap-3 t-muted" },
      el("span", { class: "spin" }, icon("loader")), "Loading…"));
}

function errorNode(message) {
  return el("div", { class: "page" },
    el("div", { class: "alert alert-error" }, icon("alertCircle"), el("div", {}, message)));
}

let _renderSeq = 0;

async function render() {
  const seq = ++_renderSeq;
  const { path, query } = parseHash();

  // Token-driven context: a review_token means an SME deep-link; a job_token
  // on the dashboard means a requestor deep-link.
  if (query.review_token) {
    state.set({ reviewToken: query.review_token, userType: "sme" });
  }
  if (query.job_token) {
    state.set({ jobToken: query.job_token, userType: "requestor" });
  }

  const route = ROUTES[path] || ROUTES["#/"];
  if (route.role && !query.review_token && !query.job_token) {
    state.set({ userType: route.role });
  }

  const app = document.getElementById("app");
  const ctx = { navigate, query, path };

  // Mount layout with a loading placeholder immediately for responsiveness.
  app.replaceChildren(layout(loadingNode(), navigate, path));

  let pageNode;
  try {
    pageNode = await route.mod.render(ctx);
  } catch (e) {
    pageNode = errorNode(e && e.message ? e.message : "Failed to load this page.");
  }
  if (seq !== _renderSeq) return; // a newer navigation superseded this one
  app.replaceChildren(layout(pageNode, navigate, path));
  window.scrollTo(0, 0);
}

export function startRouter() {
  window.addEventListener("hashchange", render);
  // Best-effort: learn mock/live mode from the backend health endpoint.
  api.healthCheck()
    .then((h) => state.set({ mockMode: !!h.mock_mode }))
    .catch(() => {})
    .finally(() => render());
}
