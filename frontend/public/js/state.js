// Tiny client-side store. Persists job/review context to localStorage so a
// page refresh keeps the user in the same flow.

const LS_KEY = "genpal_state_v1";

const defaults = {
  userType: "requestor", // "requestor" | "sme"
  jobId: null,
  jobToken: null,
  reviewToken: null,
  // transient caches (not persisted)
  job: null,
  dashboard: null,
  reviewSession: null,
  selectedQuestionId: null,
  lastVersion: null,
  mockMode: true,
};

function loadPersisted() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return {
      userType: parsed.userType,
      jobId: parsed.jobId,
      jobToken: parsed.jobToken,
      reviewToken: parsed.reviewToken,
    };
  } catch {
    return {};
  }
}

const _state = { ...defaults, ...loadPersisted() };
const _listeners = new Set();

function persist() {
  try {
    localStorage.setItem(
      LS_KEY,
      JSON.stringify({
        userType: _state.userType,
        jobId: _state.jobId,
        jobToken: _state.jobToken,
        reviewToken: _state.reviewToken,
      })
    );
  } catch {
    /* ignore quota / private-mode errors */
  }
}

export const state = {
  get(key) {
    return key ? _state[key] : _state;
  },
  set(patch) {
    Object.assign(_state, patch);
    persist();
    _listeners.forEach((fn) => fn(_state));
  },
  subscribe(fn) {
    _listeners.add(fn);
    return () => _listeners.delete(fn);
  },
  reset() {
    Object.assign(_state, {
      jobId: null,
      jobToken: null,
      reviewToken: null,
      job: null,
      dashboard: null,
      reviewSession: null,
      selectedQuestionId: null,
      lastVersion: null,
    });
    persist();
  },
};
