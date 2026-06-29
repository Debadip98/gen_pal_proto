import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import {
  ArrowRight,
  FileInput,
  Search,
  Sparkles,
  CheckCircle2,
  UserCheck,
  RefreshCw,
  Download,
  BarChart3,
} from "lucide-react";

const flowSteps = [
  {
    id: 1,
    title: "Request Intake",
    description: "User enters skill, SSID, topics, URLs, counts, and SME email.",
    icon: FileInput,
    color: "bg-blue-600",
    details: [
      "Enter Skill Name and SSID",
      "Add Requestor and SME emails",
      "Paste topic list (one per line)",
      "Add reference URLs",
      "Configure career levels and question counts",
    ],
  },
  {
    id: 2,
    title: "Documentation Enrichment",
    description: "System uses pasted URLs and optionally searches latest docs.",
    icon: Search,
    color: "bg-indigo-600",
    details: [
      "Manual URLs always included",
      "Auto-discovery of latest official docs",
      "Relevance scoring per source",
      "User selects final doc set for generation",
    ],
  },
  {
    id: 3,
    title: "AI Question Generation",
    description: "System generates QnA records by career level.",
    icon: Sparkles,
    color: "bg-[#A100FF]",
    details: [
      "Sequential generation by career level",
      "Configurable question count per level",
      "Context-rich, role-specific scenarios",
      "Real-time progress tracking with event log",
    ],
  },
  {
    id: 4,
    title: "Duplicate and Format Validation",
    description: "System checks schema, duplicates, and similarity.",
    icon: CheckCircle2,
    color: "bg-green-600",
    details: [
      "Embedding-based similarity detection",
      "Automatic rework for high-similarity pairs",
      "Schema validation — 11 columns, Sheet1",
      "Serial numbering and field presence checks",
    ],
  },
  {
    id: 5,
    title: "SME Review",
    description: "SME accepts, rejects, or regenerates each question.",
    icon: UserCheck,
    color: "bg-amber-600",
    details: [
      "Secure tokenized review link via email",
      "Question-by-question accept/reject workflow",
      "LLM suggestion box for each question",
      "Filter queue by status or alignment",
    ],
  },
  {
    id: 6,
    title: "Question-Level Rework",
    description: "Only selected question is regenerated using SME feedback and docs.",
    icon: RefreshCw,
    color: "bg-orange-600",
    details: [
      "Only one question reworked at a time",
      "All other questions preserved",
      "Pre-filled from SME feedback or LLM suggestion",
      "Side-by-side version comparison before final decision",
    ],
  },
  {
    id: 7,
    title: "GenPal Excel Export",
    description: "System creates one Sheet1 Excel file with 11 columns.",
    icon: Download,
    color: "bg-teal-600",
    details: [
      "Single workbook, single sheet (Sheet1)",
      "11 columns in exact order",
      "No review metadata exported",
      "Draft and Approved versions available",
    ],
  },
  {
    id: 8,
    title: "Decision Evidence",
    description: "System shows cost, traceability, notifications, and review status.",
    icon: BarChart3,
    color: "bg-pink-600",
    details: [
      "Detailed API cost breakdown",
      "LangSmith trace links for observability",
      "Full duplicate detection findings",
      "Runtime and performance metrics",
    ],
  },
];

export function BusinessFlow() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState<number | null>(null);

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">Business Flow Overview</h2>
        <p className="text-sm text-gray-600">
          Executive-friendly visualization of the end-to-end GenPal question bank generation process.
        </p>
      </div>

      {/* Horizontal Flow */}
      <Card>
        <CardHeader>
          <CardTitle>End-to-End Process</CardTitle>
          <p className="text-xs text-gray-500">Click any stage to view details.</p>
        </CardHeader>
        <CardContent>
          <div className="flex items-start gap-2 overflow-x-auto pb-4">
            {flowSteps.map((step, index) => {
              const Icon = step.icon;
              const isActive = activeStep === step.id;
              return (
                <div key={step.id} className="flex items-start gap-2 shrink-0">
                  <button
                    onClick={() => setActiveStep(activeStep === step.id ? null : step.id)}
                    className={`flex flex-col items-center gap-2 rounded-xl border-2 p-3 w-32 transition-all ${
                      isActive
                        ? "border-[#A100FF] bg-[#A100FF]/5 shadow-md"
                        : "border-[#D9D9E3] bg-white hover:border-[#A100FF] hover:shadow-sm"
                    }`}
                  >
                    <div className={`${step.color} rounded-full p-2.5`}>
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-[#D9D9E3] text-xs text-[#1F1F29]">
                      {step.id}
                    </div>
                    <p className="text-center text-xs text-[#1F1F29] leading-tight">{step.title}</p>
                    <p className="text-center text-[10px] text-gray-500 leading-tight">{step.description}</p>
                  </button>
                  {index < flowSteps.length - 1 && (
                    <div className="mt-10 shrink-0">
                      <ArrowRight className="h-4 w-4 text-[#D9D9E3]" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Expanded details panel */}
          {activeStep !== null && (() => {
            const step = flowSteps.find((s) => s.id === activeStep)!;
            const Icon = step.icon;
            return (
              <div className="mt-4 rounded-xl border-2 border-[#A100FF] bg-[#F7F7FA] p-5">
                <div className="flex items-center gap-3 mb-3">
                  <div className={`${step.color} rounded-full p-2`}>
                    <Icon className="h-5 w-5 text-white" />
                  </div>
                  <p className="text-sm text-[#1F1F29]">Stage {step.id}: {step.title}</p>
                </div>
                <ul className="grid grid-cols-2 gap-x-6 gap-y-1">
                  {step.details.map((d, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                      <span className="mt-0.5 text-[#A100FF] shrink-0">•</span>{d}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })()}
        </CardContent>
      </Card>

      {/* Key Benefits */}
      <Card className="border-2 border-[#A100FF]">
        <CardHeader>
          <CardTitle>Key Benefits</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-1">
              <h4 className="text-sm text-[#1F1F29]">Speed</h4>
              <p className="text-xs text-gray-600">Generate 280 questions in ~18 minutes vs. days of manual work.</p>
            </div>
            <div className="space-y-1">
              <h4 className="text-sm text-[#1F1F29]">Quality</h4>
              <p className="text-xs text-gray-600">AI-powered duplicate detection with SME review and LLM suggestions.</p>
            </div>
            <div className="space-y-1">
              <h4 className="text-sm text-[#1F1F29]">Transparency</h4>
              <p className="text-xs text-gray-600">Full cost tracking, traceability, and human review workflow.</p>
            </div>
            <div className="space-y-1">
              <h4 className="text-sm text-[#1F1F29]">Compliance</h4>
              <p className="text-xs text-gray-600">GenPal-validated schema, 11 exact columns, no metadata leakage.</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={() => navigate("/cost")}>
          Back to Cost Summary
        </Button>
        <Button onClick={() => navigate("/")} className="bg-[#A100FF] hover:bg-[#8A00DD]">
          Back to Home
        </Button>
      </div>
    </div>
  );
}
