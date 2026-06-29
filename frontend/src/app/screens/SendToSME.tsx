import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { CheckCircle2, Copy, Mail, Send, Loader2 } from "lucide-react";
import { api } from "../services/api";
import { useJob } from "../context/JobContext";

export function SendToSME() {
  const navigate = useNavigate();
  const { jobId, setReviewToken } = useJob();
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [reviewLink, setReviewLink] = useState<string | null>(null);

  const appBase = (import.meta.env.VITE_APP_BASE_URL as string | undefined) ?? "http://localhost:8501";

  const handleSend = async () => {
    if (!jobId) { setError("No active job found. Go back and generate a question bank first."); return; }
    setLoading(true);
    setError(null);
    try {
      const res = await api.sendSmeReview(jobId);
      const token = res.review_token;
      setReviewToken(token);
      const link = `${appBase}/?review_token=${token}`;
      setReviewLink(link);
      setSent(true);
      setTimeout(() => navigate("/dashboard"), 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send review.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (reviewLink) { navigator.clipboard.writeText(reviewLink); setCopied(true); setTimeout(() => setCopied(false), 2000); }
  };

  const displayLink = reviewLink ?? `${appBase}/?review_token=<pending>`;

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">Send to SME Review</h2>
        <p className="text-sm text-gray-600">Send the secure review link to the SME for question-by-question review.</p>
      </div>

      {error && <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>}

      <Card>
        <CardHeader><CardTitle className="text-base">Review Link</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2 rounded-lg border border-[#D9D9E3] bg-[#F7F7FA] px-4 py-3">
            <code className="flex-1 text-xs text-blue-600 break-all">{displayLink}</code>
            <Button variant="ghost" size="sm" onClick={handleCopy} className="shrink-0" disabled={!reviewLink}>
              {copied ? <CheckCircle2 className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
          <p className="text-xs text-gray-500">This link grants secure SME access to the review workspace. It is valid for 7 days.</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Mail className="h-4 w-4 text-[#A100FF]" />Email Preview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-[#D9D9E3] bg-[#F7F7FA] p-5 space-y-3">
            <div className="space-y-1">
              <div className="flex gap-2 text-xs"><span className="text-gray-500 w-12">To:</span><span className="text-[#1F1F29]">sme@example.com</span></div>
              <div className="flex gap-2 text-xs"><span className="text-gray-500 w-12">Subject:</span><span className="text-[#1F1F29]">GenPal Question Bank Review Required</span></div>
            </div>
            <div className="border-t border-[#D9D9E3] pt-3 space-y-2 text-sm text-[#1F1F29]">
              <p>Dear SME,</p>
              <p>A GenPal question bank has been generated and requires your expert review.</p>
              <p>Please use the secure review link below to access the SME Review Workspace:</p>
              <p className="rounded bg-white border border-[#D9D9E3] px-3 py-2 text-xs text-blue-600 break-all">{displayLink}</p>
              <p className="text-xs text-gray-500">This link is valid for 7 days.</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {sent && (
        <Card className="border-green-600 bg-green-50">
          <CardContent className="pt-5">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
              <div>
                <p className="text-sm text-green-800">SME review link sent successfully.</p>
                <p className="text-xs text-green-700">Redirecting to dashboard in 3 seconds…</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-between">
        <Button variant="outline" onClick={() => navigate("/dashboard")}>Back to Dashboard</Button>
        <div className="flex gap-3">
          <Button variant="outline" onClick={handleCopy} disabled={!reviewLink}>
            <Copy className="mr-2 h-4 w-4" />{copied ? "Copied!" : "Copy Review Link"}
          </Button>
          <Button onClick={handleSend} disabled={loading || sent} className="bg-[#A100FF] hover:bg-[#8A00DD]">
            {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Sending…</> : <><Send className="mr-2 h-4 w-4" />Send SME Review Email</>}
          </Button>
        </div>
      </div>
    </div>
  );
}
