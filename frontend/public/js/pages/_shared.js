// Shared helpers for page modules: status -> badge mappings that match the
// backend constants (QuestionStatus / VersionStatus).
import { badge } from "../components.js";

const Q_STATUS = {
  DRAFT: ["Draft", "gray"],
  PENDING_SME_REVIEW: ["Pending Review", "outline-amber"],
  PENDING_REVIEW: ["Pending Review", "outline-amber"],
  ACCEPTED: ["Accepted", "success"],
  REJECTED: ["Rejected", "outline-red"],
  REGENERATED: ["Regenerated", "outline-blue"],
  MANUAL_REVIEW_REQUIRED: ["Manual Review", "outline-red"],
};

export function questionStatusBadge(status) {
  const [label, variant] = Q_STATUS[status] || [status, "gray"];
  return badge(label, variant);
}

export function statusLabel(status) {
  return (Q_STATUS[status] || [status])[0];
}
