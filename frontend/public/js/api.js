// Centralized API client. All paths are RELATIVE (/api/v1/...) so the browser
// talks only to Apache, which reverse-proxies to FastAPI. No hard-coded host.

const BASE = "/api/v1";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function friendly(status, detail) {
  if (status === 0) {
    return "Cannot reach the backend. Make sure the FastAPI server is running and Apache is proxying /api.";
  }
  if (status === 404) return detail || "Not found.";
  if (status === 409) return detail || "This action conflicts with the current state.";
  if (status === 403) return detail || "This link is no longer valid or has expired.";
  if (status >= 500) return detail || "The server hit an error. Check the backend terminal/logs.";
  return detail || `Request failed (HTTP ${status}).`;
}

async function request(path, { method = "GET", body, query } = {}) {
  let url = `${BASE}${path}`;
  if (query) {
    const qs = new URLSearchParams(query).toString();
    if (qs) url += `?${qs}`;
  }
  let res;
  try {
    res = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(friendly(0), 0);
  }

  if (!res.ok) {
    let detail = "";
    try {
      const data = await res.json();
      detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(friendly(res.status, detail), res.status);
  }

  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res;
}

export { ApiError };

export const api = {
  // --- Health ---
  healthCheck: () => request("/health"),

  // --- Jobs ---
  createJob: (payload) => request("/jobs", { method: "POST", body: payload }),
  getJob: (jobId) => request(`/jobs/${jobId}`),
  getQuestions: (jobId, params) => request(`/jobs/${jobId}/questions`, { query: params }),
  generateQuestions: (jobId) => request(`/jobs/${jobId}/generate`, { method: "POST" }),
  getCostSummary: (jobId) => request(`/jobs/${jobId}/cost-summary`),

  // --- Docs ---
  discoverDocs: (jobId) => request(`/jobs/${jobId}/discover-docs`, { method: "POST" }),
  selectDocs: (jobId, sourceIds) =>
    request(`/jobs/${jobId}/select-docs`, {
      method: "POST",
      body: { selected_source_ids: sourceIds },
    }),

  // --- SME review handoff ---
  sendSmeReview: (jobId) => request(`/jobs/${jobId}/send-sme-review`, { method: "POST" }),

  // --- Review session (SME) ---
  getReviewSession: (token) => request(`/review/${token}`),
  acceptQuestion: (token, questionId) =>
    request(`/review/${token}/questions/${questionId}/accept`, { method: "POST" }),
  rejectQuestion: (token, questionId, comment) =>
    request(`/review/${token}/questions/${questionId}/reject`, {
      method: "POST",
      body: { comment },
    }),
  generateSuggestion: (token, questionId) =>
    request(`/review/${token}/questions/${questionId}/suggestion`, { method: "POST" }),
  regenerateQuestion: (token, questionId, feedback, useLlmSuggestion = false) =>
    request(`/review/${token}/questions/${questionId}/regenerate`, {
      method: "POST",
      body: { sme_feedback: feedback, use_llm_suggestion: useLlmSuggestion },
    }),
  acceptVersion: (token, versionId) =>
    request(`/review/${token}/versions/${versionId}/accept`, { method: "POST" }),
  rejectVersion: (token, versionId) =>
    request(`/review/${token}/versions/${versionId}/reject`, { method: "POST" }),

  // --- Requestor dashboard ---
  getDashboard: (jobToken) => request(`/dashboard/${jobToken}`),
  getNotifications: (jobToken) => request(`/dashboard/${jobToken}/notifications`),
  markNotificationRead: (jobToken, notificationId) =>
    request(`/dashboard/${jobToken}/notifications/${notificationId}/read`, { method: "POST" }),
  markAllNotificationsRead: (jobToken) =>
    request(`/dashboard/${jobToken}/notifications/read-all`, { method: "POST" }),

  // --- Excel export: trigger a browser download via the proxied endpoint ---
  exportExcel(jobId, exportType = "draft") {
    // Navigating to the URL lets the browser handle the file download using
    // the Content-Disposition header returned by FastAPI (through Apache).
    const url = `${BASE}/jobs/${jobId}/export?type=${encodeURIComponent(exportType)}`;
    const a = document.createElement("a");
    a.href = url;
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
  },
};
