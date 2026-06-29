import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { Button } from "../components/ui/button";
import { CheckCircle2, Clock, Loader2, Copy, AlertCircle, Lock } from "lucide-react";
import { api, type Job } from "../services/api";
import { useJob } from "../context/JobContext";

const getStatusIcon = (status: string) => {
  switch (status) {
    case "locked": return <Lock className="h-4 w-4 text-[#A100FF]" />;
    case "generating": return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />;
    case "duplicate-check-running": return <Copy className="h-4 w-4 text-amber-600" />;
    case "reworking": return <Loader2 className="h-4 w-4 animate-spin text-amber-600" />;
    case "manual-review": return <AlertCircle className="h-4 w-4 text-red-600" />;
    case "pending": return <Clock className="h-4 w-4 text-gray-400" />;
    default: return <CheckCircle2 className="h-4 w-4 text-green-600" />;
  }
};

const getStatusBadge = (status: string) => {
  switch (status) {
    case "locked": return <Badge className="bg-[#A100FF]"><CheckCircle2 className="mr-1 h-3 w-3" />Locked</Badge>;
    case "generating": return <Badge variant="outline" className="border-blue-600 text-blue-600">Generating</Badge>;
    case "duplicate-check-running": return <Badge variant="outline" className="border-amber-600 text-amber-600">Duplicate Check Running</Badge>;
    case "reworking": return <Badge variant="outline" className="border-amber-600 text-amber-600">Reworking Similar Questions</Badge>;
    case "manual-review": return <Badge variant="outline" className="border-red-600 text-red-600">Manual Review</Badge>;
    case "pending": return <Badge variant="secondary">Pending</Badge>;
    default: return <Badge variant="secondary">{status}</Badge>;
  }
};

export function GenerationProgress() {
  const navigate = useNavigate();
  const { jobId } = useJob();
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [started, setStarted] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const startAndPoll = async () => {
      try {
        if (!started) {
          setStarted(true);
          await api.startGeneration(jobId);
        }
        const j = await api.getJob(jobId);
        setJob(j);
        if (j.status === "completed" || j.status === "failed") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          if (j.status === "completed") setTimeout(() => navigate("/dashboard"), 1500);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Generation error.");
        if (intervalRef.current) clearInterval(intervalRef.current);
      }
    };

    startAndPoll();
    intervalRef.current = setInterval(startAndPoll, 3000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [jobId]);

  const isRunning = job ? !["completed", "failed"].includes(job.status) : true;

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">Generation Progress</h2>
        <p className="text-sm text-gray-600">Sequential question generation by career level with duplicate detection.</p>
      </div>

      {error && <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>}

      {!jobId && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          No active job found. <button className="underline" onClick={() => navigate("/")}>Go back to Input</button> to create one.
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-5">
        <Card><CardContent className="pt-6"><div className="text-center"><p className="text-2xl text-[#1F1F29]">{job?.status ?? "—"}</p><p className="text-xs text-gray-500">Job Status</p></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-center"><p className="text-2xl text-[#1F1F29]">{job?.skill_name?.slice(0, 6) ?? "—"}</p><p className="text-xs text-gray-500">Skill</p></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-center"><p className="text-2xl text-[#1F1F29]">{job?.id?.slice(0, 8) ?? "—"}</p><p className="text-xs text-gray-500">Job ID</p></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-center"><p className="text-2xl text-[#1F1F29]">{job?.skill_id ?? "—"}</p><p className="text-xs text-gray-500">SSID</p></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-center"><p className="text-2xl text-[#1F1F29]">{isRunning ? "Running" : "Done"}</p><p className="text-xs text-gray-500">Pipeline</p></div></CardContent></Card>
      </div>

      {isRunning && (
        <div className="flex items-center gap-3 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3">
          <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
          <p className="text-sm text-blue-800">Generating questions… this may take several minutes.</p>
        </div>
      )}
      {job?.status === "completed" && (
        <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 px-4 py-3">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <p className="text-sm text-green-800">Generation complete! Redirecting to dashboard…</p>
        </div>
      )}

      <Card>
        <CardHeader><CardTitle>Job Status</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Progress</span>
              <span className="text-[#1F1F29]">{job?.status ?? "waiting"}</span>
            </div>
            <Progress value={job?.status === "completed" ? 100 : job?.status === "generating" ? 50 : 10} className="h-2 [&>div]:bg-[#A100FF]" />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2 rounded-lg bg-[#F7F7FA] p-4">
              <p className="text-xs text-gray-500">Skill Name</p>
              <p className="text-lg text-[#1F1F29]">{job?.skill_name ?? "—"}</p>
            </div>
            <div className="space-y-2 rounded-lg bg-[#F7F7FA] p-4">
              <p className="text-xs text-gray-500">Status</p>
              <p className="text-lg text-[#1F1F29]">{job?.status ?? "—"}</p>
            </div>
            <div className="space-y-2 rounded-lg bg-[#F7F7FA] p-4">
              <p className="text-xs text-gray-500">SME Email</p>
              <p className="text-lg text-[#1F1F29]">{job?.sme_email ?? "—"}</p>
            </div>
            <div className="space-y-2 rounded-lg bg-[#F7F7FA] p-4">
              <p className="text-xs text-gray-500">Last Updated</p>
              <p className="text-lg text-[#1F1F29]">{job?.updated_at ? new Date(job.updated_at).toLocaleTimeString() : "—"}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-3">
        <Button onClick={() => navigate("/dashboard")} className="bg-[#A100FF] hover:bg-[#8A00DD]">
          View Requestor Dashboard
        </Button>
      </div>
    </div>
  );
}
