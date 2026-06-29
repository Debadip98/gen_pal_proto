import { createContext, useContext, useState } from "react";

interface JobContextValue {
  jobId: string | null;
  jobToken: string | null;
  reviewToken: string | null;
  setJob: (id: string, token: string) => void;
  setReviewToken: (token: string) => void;
}

const JobContext = createContext<JobContextValue | null>(null);

export function JobProvider({ children }: { children: React.ReactNode }) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobToken, setJobToken] = useState<string | null>(null);
  const [reviewToken, setReviewToken] = useState<string | null>(null);

  const setJob = (id: string, token: string) => { setJobId(id); setJobToken(token); };

  return (
    <JobContext.Provider value={{ jobId, jobToken, reviewToken, setJob, setReviewToken }}>
      {children}
    </JobContext.Provider>
  );
}

export function useJob() {
  const ctx = useContext(JobContext);
  if (!ctx) throw new Error("useJob must be used inside JobProvider");
  return ctx;
}
