const BASE = `${(import.meta.env.VITE_BACKEND_URL as string | undefined) ?? "http://localhost:8080"}/api/v1`;

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = `${method} ${path} → ${res.status}`;
    try { const j = await res.json(); detail = j.detail ?? detail; } catch { /**/ }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => req<{ status: string }>("GET", "/health"),
  createJob: (p: CreateJobPayload) => req<Job>("POST", "/jobs", p),
  getJob: (id: string) => req<Job>("GET", `/jobs/${id}`),
  getQuestions: (id: string, params?: { career_level?: string; status?: string }) => {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    return req<Question[]>("GET", `/jobs/${id}/questions${qs ? "?" + qs : ""}`);
  },
  startGeneration: (id: string) => req<Job>("POST", `/jobs/${id}/generate`),
  discoverDocs: (id: string) => req<{ sources: DocSource[] }>("POST", `/jobs/${id}/discover-docs`),
  selectDocs: (id: string, selected_source_ids: string[]) =>
    req<Job>("POST", `/jobs/${id}/select-docs`, { selected_source_ids }),
  sendSmeReview: (id: string) =>
    req<{ review_token: string }>("POST", `/jobs/${id}/send-sme-review`),
  getExport: async (id: string, type: "draft" | "approved" = "draft"): Promise<Blob> => {
    const res = await fetch(`${BASE}/jobs/${id}/export?type=${type}`);
    if (!res.ok) throw new Error(`export → ${res.status}`);
    return res.blob();
  },
  getCostSummary: (id: string) => req<CostSummary>("GET", `/jobs/${id}/cost-summary`),
  getReviewSession: (token: string) => req<ReviewSession>("GET", `/review/${token}`),
  acceptQuestion: (token: string, qId: string) =>
    req("POST", `/review/${token}/questions/${qId}/accept`),
  rejectQuestion: (token: string, qId: string, comment: string) =>
    req("POST", `/review/${token}/questions/${qId}/reject`, { comment }),
  getSuggestion: (token: string, qId: string) =>
    req("POST", `/review/${token}/questions/${qId}/suggestion`),
  regenerateQuestion: (token: string, qId: string, sme_feedback: string, use_llm_suggestion: boolean) =>
    req("POST", `/review/${token}/questions/${qId}/regenerate`, { sme_feedback, use_llm_suggestion }),
  acceptVersion: (token: string, vId: string) =>
    req("POST", `/review/${token}/versions/${vId}/accept`),
  rejectVersion: (token: string, vId: string) =>
    req("POST", `/review/${token}/versions/${vId}/reject`),
  getDashboard: (jobToken: string) => req<DashboardData>("GET", `/dashboard/${jobToken}`),
  getNotifications: (jobToken: string) =>
    req<Notification[]>("GET", `/dashboard/${jobToken}/notifications`),
  markNotificationRead: (jobToken: string, nId: string) =>
    req("POST", `/dashboard/${jobToken}/notifications/${nId}/read`),
  markAllNotificationsRead: (jobToken: string) =>
    req("POST", `/dashboard/${jobToken}/notifications/read-all`),
};

export interface CreateJobPayload {
  skill_name: string; skill_id: string; requestor_email: string; sme_email: string;
  topics: string[]; reference_urls: string[];
  career_levels: Record<string, number>;
  duplicate_threshold: number; auto_find_docs: boolean;
}
export interface Job {
  id: string; job_token: string; skill_name: string; skill_id: string;
  requestor_email: string; sme_email: string; status: string;
  created_at: string; updated_at: string;
}
export interface Question {
  id: string; title: string; topic: string; career_level: string;
  complexity: string; question: string; answer: string;
  reference_url: string; status: string; duplicate_warning: boolean;
  doc_alignment: string; sme_feedback: string; last_sme_action: string;
}
export interface DocSource {
  id: string; title: string; url: string; domain: string;
  relevance: string; source_type: string; summary: string;
}
export interface CostSummary {
  total_cost_usd: number; generation_cost: number; embedding_cost: number;
  total_tokens: number; input_tokens: number; output_tokens: number;
}
export interface ReviewSession {
  job: Job; questions: Question[]; review_token: string;
  expires_at: string; status: string;
}
export interface DashboardData {
  job: Job; questions: Question[]; sme_review_status: string;
  accepted: number; rejected: number; pending: number; total: number;
}
export interface Notification {
  id: string; message: string; action: string; read: boolean;
  question_id: string | null; created_at: string;
}
