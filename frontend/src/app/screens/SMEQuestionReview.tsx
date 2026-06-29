import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import { CheckCircle2, X, RefreshCw, Sparkles, ChevronLeft, ChevronRight, ArrowLeft } from "lucide-react";

export function SMEQuestionReview() {
  const navigate = useNavigate();
  const [feedback, setFeedback] = useState("");
  const [decision, setDecision] = useState<string | null>(null);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h2 className="text-2xl text-[#1F1F29]">Question Review</h2>
          <p className="text-sm text-gray-600">Question 4 of 80 — SharePoint Security and Permissions</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => navigate("/sme-review")}>
            <ArrowLeft className="mr-1 h-3 w-3" />
            Back to Queue
          </Button>
        </div>
      </div>

      {/* Question metadata */}
      <Card>
        <CardContent className="pt-5">
          <div className="grid gap-3 md:grid-cols-4 lg:grid-cols-7">
            {[
              { label: "title", value: "4" },
              { label: "topic", value: "SharePoint Security and Permissions" },
              { label: "career_level", value: <Badge variant="outline" className="text-xs">SSE</Badge> },
              { label: "complexity", value: <Badge variant="secondary" className="text-xs">Proficient</Badge> },
              { label: "reference_url", value: <span className="text-xs text-blue-600">learn.microsoft.com</span> },
              { label: "duplicate_warning", value: <Badge variant="outline" className="border-amber-600 text-amber-600 text-xs">Yes</Badge> },
              { label: "doc_alignment", value: <Badge className="bg-green-600 text-xs">Aligned</Badge> },
            ].map((item) => (
              <div key={item.label}>
                <p className="text-[10px] text-gray-500 font-mono">{item.label}</p>
                <div className="mt-0.5 text-sm">{item.value}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main question card */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Question</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-[#1F1F29] leading-relaxed">
                A senior engineer needs to implement custom permission levels for a site collection that meets compliance requirements while restricting document export capabilities. What is the most appropriate approach to design and enforce this?
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Answer</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-[#1F1F29] leading-relaxed">
                Create a custom permission level via Site Settings → Site Permissions → Permission Levels. Select appropriate base permissions, explicitly deny the "Use Remote Interfaces" and "Use Client Integration Features" to restrict export. Assign the custom level to the relevant SharePoint groups and verify inheritance breaks at the list level where needed.
              </p>
            </CardContent>
          </Card>

          {/* SME comment box */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">SME Feedback / Review Instruction</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Make this question more relevant to Oracle RAC failover or SharePoint farm recovery."
                className="min-h-24"
              />
              <p className="text-xs text-gray-500">Your feedback will be used to regenerate this question if you choose to rework it.</p>
            </CardContent>
          </Card>

          {/* Decision buttons */}
          {decision && (
            <Card className="border-green-600 bg-green-50">
              <CardContent className="pt-4">
                <p className="text-sm text-green-800">
                  {decision === "accepted" && "Question accepted. Moving to next question."}
                  {decision === "rejected" && "Question rejected. Feedback saved."}
                  {decision === "regenerated" && "Redirecting to regeneration screen..."}
                </p>
              </CardContent>
            </Card>
          )}

          <div className="flex gap-3 flex-wrap">
            <Button
              className="bg-green-600 hover:bg-green-700"
              onClick={() => { setDecision("accepted"); setTimeout(() => navigate("/sme-review"), 1000); }}
            >
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Accept Question
            </Button>
            <Button
              variant="outline"
              className="border-red-600 text-red-600 hover:bg-red-50"
              onClick={() => setDecision("rejected")}
            >
              <X className="mr-2 h-4 w-4" />
              Reject Question
            </Button>
            <Button
              variant="outline"
              className="border-amber-600 text-amber-700 hover:bg-amber-50"
              onClick={() => { setDecision("regenerated"); setTimeout(() => navigate("/regenerate"), 800); }}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Regenerate Question
            </Button>
          </div>
        </div>

        {/* LLM Review Suggestion */}
        <div>
          <Card className="border-[#A100FF] h-full">
            <CardHeader className="bg-[#A100FF]/5">
              <CardTitle className="flex items-center gap-2 text-base">
                <Sparkles className="h-4 w-4 text-[#A100FF]" />
                LLM Review Suggestion
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              {[
                { label: "Quality Summary", value: "Good coverage of SharePoint permissions, clear scenario." },
                { label: "Possible Concern", value: "Scenario resembles another access-control question (Q2). Similarity: 0.88." },
                { label: "Suggested Improvement", value: "Consider regenerating with a deployment or governance scenario to differentiate." },
                { label: "Documentation Alignment", value: "Aligned with learn.microsoft.com permissions documentation." },
                { label: "Recommended Action", value: "Regenerate with different scenario context." },
                { label: "SME-Friendly Message", value: "This question is aligned with the SharePoint permissions topic, but the scenario resembles another access-control question. Consider regenerating it with a deployment or governance scenario." },
              ].map((item) => (
                <div key={item.label} className="space-y-1">
                  <p className="text-xs text-gray-500">{item.label}</p>
                  <p className="text-xs text-[#1F1F29]">{item.value}</p>
                </div>
              ))}
              <Button
                variant="outline"
                size="sm"
                className="w-full border-[#A100FF] text-[#A100FF]"
                onClick={() => { setFeedback("Consider regenerating with a deployment or governance scenario to differentiate from Q2."); navigate("/regenerate"); }}
              >
                <Sparkles className="mr-2 h-3 w-3" />
                Use Suggestion for Regeneration
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button variant="outline" size="sm">
          <ChevronLeft className="mr-1 h-4 w-4" />
          Previous Question
        </Button>
        <Button variant="outline" size="sm" onClick={() => navigate("/sme-question")}>
          Next Question
          <ChevronRight className="ml-1 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
