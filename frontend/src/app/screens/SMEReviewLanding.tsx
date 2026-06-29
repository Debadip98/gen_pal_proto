import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../components/ui/table";
import { CheckCircle2, X, RefreshCw, AlertTriangle, BookOpen } from "lucide-react";

const questions = [
  { title: 1, topic: "SharePoint Farm Architecture", career_level: "ASE", complexity: "Basic", status: "pending", dup_warning: false, doc_alignment: "Aligned" },
  { title: 2, topic: "SharePoint Object Model", career_level: "ASE", complexity: "Proficient", status: "accepted", dup_warning: false, doc_alignment: "Aligned" },
  { title: 3, topic: "SharePoint Search Config", career_level: "SE", complexity: "Advanced", status: "pending", dup_warning: false, doc_alignment: "Partial" },
  { title: 4, topic: "SharePoint Security", career_level: "SSE", complexity: "Proficient", status: "pending", dup_warning: true, doc_alignment: "Aligned" },
  { title: 5, topic: "SharePoint Farm Architecture", career_level: "SE", complexity: "Basic", status: "rejected", dup_warning: false, doc_alignment: "Not Aligned" },
  { title: 6, topic: "SharePoint Object Model", career_level: "SSE", complexity: "Advanced", status: "regenerated", dup_warning: false, doc_alignment: "Aligned" },
];

const filterChips = ["All", "Pending", "Accepted", "Rejected", "Regenerated", "Manual Review Required", "Duplicate Warning", "Doc Alignment Warning"];

const statusBadge = (s: string) => {
  switch (s) {
    case "accepted": return <Badge className="bg-green-600 text-xs"><CheckCircle2 className="mr-1 h-3 w-3" />Accepted</Badge>;
    case "rejected": return <Badge variant="outline" className="border-red-600 text-red-600 text-xs"><X className="mr-1 h-3 w-3" />Rejected</Badge>;
    case "regenerated": return <Badge variant="outline" className="border-amber-600 text-amber-600 text-xs"><RefreshCw className="mr-1 h-3 w-3" />Regenerated</Badge>;
    default: return <Badge variant="secondary" className="text-xs">Pending</Badge>;
  }
};

const alignmentBadge = (a: string) => {
  if (a === "Aligned") return <Badge className="bg-green-600 text-xs">Aligned</Badge>;
  if (a === "Partial") return <Badge variant="outline" className="border-amber-600 text-amber-600 text-xs">Partial</Badge>;
  return <Badge variant="outline" className="border-red-600 text-red-600 text-xs">Not Aligned</Badge>;
};

export function SMEReviewLanding() {
  const navigate = useNavigate();
  const [activeFilter, setActiveFilter] = useState("All");

  const filtered = activeFilter === "All"
    ? questions
    : activeFilter === "Duplicate Warning"
    ? questions.filter((q) => q.dup_warning)
    : questions.filter((q) => q.status === activeFilter.toLowerCase());

  const counts = {
    pending: questions.filter((q) => q.status === "pending").length,
    accepted: questions.filter((q) => q.status === "accepted").length,
    rejected: questions.filter((q) => q.status === "rejected").length,
    regenerated: questions.filter((q) => q.status === "regenerated").length,
  };

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">SME Review Workspace</h2>
        <p className="text-sm text-gray-600">Review generated GenPal QnA questions — accept, reject, or regenerate individual items.</p>
      </div>

      {/* Job summary */}
      <Card>
        <CardContent className="pt-5">
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
            {[
              { label: "Skill Name", value: "Microsoft SharePoint Server Development" },
              { label: "SSID", value: "80002591" },
              { label: "Total Questions", value: "80" },
              { label: "Requestor", value: "requestor@example.com" },
              { label: "Review Due", value: "2026-06-30" },
              { label: "Review Status", value: <Badge variant="outline" className="border-amber-600 text-amber-600 text-xs">In Progress</Badge> },
            ].map((item) => (
              <div key={item.label}>
                <p className="text-xs text-gray-500">{item.label}</p>
                <div className="mt-0.5 text-sm text-[#1F1F29]">{item.value}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Progress metrics */}
      <div className="grid gap-4 md:grid-cols-5">
        {[
          { label: "Pending", value: counts.pending, color: "" },
          { label: "Accepted", value: counts.accepted, color: "text-green-600" },
          { label: "Rejected", value: counts.rejected, color: "text-red-600" },
          { label: "Regenerated", value: counts.regenerated, color: "text-amber-600" },
          { label: "Manual Review", value: 0, color: "text-red-600" },
        ].map((m) => (
          <Card key={m.label}>
            <CardContent className="pt-5">
              <div className="text-center">
                <p className={`text-2xl ${m.color || "text-[#1F1F29]"}`}>{m.value}</p>
                <p className="text-xs text-gray-500">{m.label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-2">
        {filterChips.map((chip) => (
          <button
            key={chip}
            onClick={() => setActiveFilter(chip)}
            className={`rounded-full border px-3 py-1 text-xs transition-colors ${
              activeFilter === chip
                ? "border-[#A100FF] bg-[#A100FF] text-white"
                : "border-[#D9D9E3] text-gray-600 hover:border-[#A100FF]"
            }`}
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Question queue */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Question Review Queue</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>title</TableHead>
                  <TableHead>topic</TableHead>
                  <TableHead>career_level</TableHead>
                  <TableHead>complexity</TableHead>
                  <TableHead>status</TableHead>
                  <TableHead>duplicate warning</TableHead>
                  <TableHead>doc alignment</TableHead>
                  <TableHead>action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((q) => (
                  <TableRow key={q.title}>
                    <TableCell>{q.title}</TableCell>
                    <TableCell className="max-w-[160px]">
                      <p className="text-xs truncate">{q.topic}</p>
                    </TableCell>
                    <TableCell><Badge variant="outline" className="text-xs">{q.career_level}</Badge></TableCell>
                    <TableCell className="text-xs">{q.complexity}</TableCell>
                    <TableCell>{statusBadge(q.status)}</TableCell>
                    <TableCell>
                      {q.dup_warning
                        ? <AlertTriangle className="h-4 w-4 text-amber-600" />
                        : <span className="text-xs text-gray-400">—</span>}
                    </TableCell>
                    <TableCell>{alignmentBadge(q.doc_alignment)}</TableCell>
                    <TableCell>
                      <Button size="sm" variant="outline" className="text-xs border-[#A100FF] text-[#A100FF]" onClick={() => navigate("/sme-question")}>
                        Review
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={() => navigate("/send-review")}>
          Back
        </Button>
        <Button onClick={() => navigate("/sme-question")} className="bg-[#A100FF] hover:bg-[#8A00DD]">
          <BookOpen className="mr-2 h-4 w-4" />
          Start Review
        </Button>
      </div>
    </div>
  );
}
