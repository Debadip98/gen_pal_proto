import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { DollarSign, Cpu, Database, ExternalLink, Clock, CheckCircle2, ChevronDown, ChevronUp } from "lucide-react";

export function CostDashboard() {
  const navigate = useNavigate();
  const [tokenBreakdownOpen, setTokenBreakdownOpen] = useState(false);

  return (
    <div className="space-y-6 p-6">
      {/* Page Header */}
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">Cost and Traceability Summary</h2>
        <p className="text-sm text-gray-600">
          Detailed breakdown of API costs and observability metrics.
        </p>
      </div>

      {/* Top Metrics — 8 cards */}
      <div className="grid gap-4 md:grid-cols-4 lg:grid-cols-8">
        <Card>
          <CardContent className="pt-4">
            <div className="flex flex-col items-center text-center">
              <div className="rounded-full bg-[#A100FF]/10 p-2 mb-2">
                <DollarSign className="h-5 w-5 text-[#A100FF]" />
              </div>
              <p className="text-xl text-[#1F1F29]">$3.42</p>
              <p className="text-xs text-gray-500">Total Estimated Cost</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex flex-col items-center text-center">
              <div className="rounded-full bg-blue-600/10 p-2 mb-2">
                <DollarSign className="h-5 w-5 text-blue-600" />
              </div>
              <p className="text-xl text-[#1F1F29]">$2.87</p>
              <p className="text-xs text-gray-500">Generation Cost</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex flex-col items-center text-center">
              <div className="rounded-full bg-green-600/10 p-2 mb-2">
                <DollarSign className="h-5 w-5 text-green-600" />
              </div>
              <p className="text-xl text-[#1F1F29]">$0.55</p>
              <p className="text-xs text-gray-500">Embedding Cost</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex flex-col items-center text-center">
              <div className="rounded-full bg-blue-600/10 p-2 mb-2">
                <Cpu className="h-5 w-5 text-blue-600" />
              </div>
              <p className="text-xl text-[#1F1F29]">1,247</p>
              <p className="text-xs text-gray-500">Total OpenAI Calls</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex flex-col items-center text-center">
              <div className="rounded-full bg-indigo-600/10 p-2 mb-2">
                <Database className="h-5 w-5 text-indigo-600" />
              </div>
              <p className="text-xl text-[#1F1F29]">487K</p>
              <p className="text-xs text-gray-500">Total Tokens</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex flex-col items-center text-center">
              <div className="rounded-full bg-purple-600/10 p-2 mb-2">
                <DollarSign className="h-5 w-5 text-purple-600" />
              </div>
              <p className="text-xl text-[#1F1F29]">$0.08</p>
              <p className="text-xs text-gray-500">Web Search Cost</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex flex-col items-center text-center">
              <div className="rounded-full bg-amber-600/10 p-2 mb-2">
                <DollarSign className="h-5 w-5 text-amber-600" />
              </div>
              <p className="text-xl text-[#1F1F29]">$0.12</p>
              <p className="text-xs text-gray-500">Regeneration Cost</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex flex-col items-center text-center">
              <div className="rounded-full bg-green-600/10 p-2 mb-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              </div>
              <p className="text-xl text-green-700">Enabled</p>
              <p className="text-xs text-gray-500">LangSmith Trace Status</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Generation Usage */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-blue-600" />
              Generation Usage
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between rounded-lg bg-[#F7F7FA] p-3">
              <span className="text-sm text-gray-600">Model</span>
              <Badge variant="secondary" className="font-mono">
                gpt-4o
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Question Generation Calls</span>
                <span className="text-[#1F1F29]">280</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Rework Calls</span>
                <span className="text-[#1F1F29]">12</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Total Generation Calls</span>
                <span className="text-[#1F1F29]">292</span>
              </div>
            </div>
            <div className="border-t pt-3 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Prompt Tokens</span>
                <span className="text-[#1F1F29]">324,567</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Completion Tokens</span>
                <span className="text-[#1F1F29]">142,892</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Total Tokens</span>
                <span className="text-[#1F1F29]">467,459</span>
              </div>
            </div>
            <div className="rounded-lg bg-blue-600/10 p-3">
              <div className="flex justify-between">
                <span className="text-sm text-blue-900">Estimated Cost</span>
                <span className="text-lg text-blue-900">$2.87</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Embedding Usage */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-green-600" />
              Embedding Usage
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between rounded-lg bg-[#F7F7FA] p-3">
              <span className="text-sm text-gray-600">Model</span>
              <Badge variant="secondary" className="font-mono">
                text-embedding-3-small
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Initial Embeddings</span>
                <span className="text-[#1F1F29]">280</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Rework Embeddings</span>
                <span className="text-[#1F1F29]">12</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Total Embeddings</span>
                <span className="text-[#1F1F29]">292</span>
              </div>
            </div>
            <div className="border-t pt-3 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Embedding API Calls</span>
                <span className="text-[#1F1F29]">292</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Similarity Comparisons</span>
                <span className="text-[#1F1F29]">40,740</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Total Tokens</span>
                <span className="text-[#1F1F29]">19,458</span>
              </div>
            </div>
            <div className="rounded-lg bg-green-600/10 p-3">
              <div className="flex justify-between">
                <span className="text-sm text-green-900">Estimated Cost</span>
                <span className="text-lg text-green-900">$0.55</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* LangSmith Trace */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ExternalLink className="h-5 w-5 text-[#A100FF]" />
              LangSmith Trace
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Project</span>
                <Badge variant="secondary" className="font-mono">
                  genpal-prototype
                </Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Status</span>
                <Badge className="bg-green-600">
                  <CheckCircle2 className="mr-1 h-3 w-3" />
                  Enabled
                </Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Trace Sessions</span>
                <span className="text-[#1F1F29]">7</span>
              </div>
            </div>
            <div className="rounded-lg border border-[#D9D9E3] p-3">
              <p className="text-xs text-gray-500 mb-2">Trace URL</p>
              <p className="text-xs text-blue-600 break-all font-mono">
                https://smith.langchain.com/public/abc123-def456-ghi789
              </p>
            </div>
            <Button variant="outline" className="w-full">
              <ExternalLink className="mr-2 h-4 w-4" />
              Open in LangSmith
            </Button>
          </CardContent>
        </Card>

        {/* Runtime Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-amber-600" />
              Runtime Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Total Runtime</span>
                <span className="text-[#1F1F29]">18m 34s</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Generation Time</span>
                <span className="text-[#1F1F29]">14m 12s</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Duplicate Check Time</span>
                <span className="text-[#1F1F29]">3m 47s</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Validation Time</span>
                <span className="text-[#1F1F29]">35s</span>
              </div>
            </div>
            <div className="border-t pt-3 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Rows Generated</span>
                <span className="text-[#1F1F29]">280</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Duplicate Repair Passes</span>
                <span className="text-[#1F1F29]">2</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Export Status</span>
                <Badge className="bg-green-600">Ready</Badge>
              </div>
            </div>
            <div className="rounded-lg bg-amber-600/10 p-3">
              <div className="flex justify-between">
                <span className="text-sm text-amber-900">Avg Time per Question</span>
                <span className="text-lg text-amber-900">3.98s</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Token Breakdown Expandable */}
      <Card>
        <CardContent className="pt-6">
          <button
            className="flex w-full items-center justify-between"
            onClick={() => setTokenBreakdownOpen((v) => !v)}
          >
            <span className="text-sm text-[#1F1F29]">View Token Breakdown</span>
            {tokenBreakdownOpen ? (
              <ChevronUp className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronDown className="h-4 w-4 text-gray-500" />
            )}
          </button>
          {tokenBreakdownOpen && (
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <div className="space-y-2 rounded-lg bg-[#F7F7FA] p-4">
                <p className="text-xs text-gray-500">Generation — gpt-4o</p>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Prompt tokens</span>
                  <span className="text-[#1F1F29]">324,567</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Completion tokens</span>
                  <span className="text-[#1F1F29]">142,892</span>
                </div>
                <div className="flex justify-between text-sm border-t pt-2">
                  <span className="text-gray-600">Estimated cost</span>
                  <span className="text-blue-700">$2.87</span>
                </div>
              </div>
              <div className="space-y-2 rounded-lg bg-[#F7F7FA] p-4">
                <p className="text-xs text-gray-500">Embedding — text-embedding-3-small</p>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Embedded questions</span>
                  <span className="text-[#1F1F29]">292</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Total tokens</span>
                  <span className="text-[#1F1F29]">19,458</span>
                </div>
                <div className="flex justify-between text-sm border-t pt-2">
                  <span className="text-gray-600">Estimated cost</span>
                  <span className="text-green-700">$0.55</span>
                </div>
              </div>
              <div className="space-y-2 rounded-lg bg-[#F7F7FA] p-4">
                <p className="text-xs text-gray-500">Grand Total</p>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">All tokens</span>
                  <span className="text-[#1F1F29]">486,917</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Total API calls</span>
                  <span className="text-[#1F1F29]">1,247</span>
                </div>
                <div className="flex justify-between text-sm border-t pt-2">
                  <span className="text-gray-600">Total cost</span>
                  <span className="text-[#A100FF]">$3.42</span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Total Cost Summary */}
      <Card className="border-2 border-[#A100FF]">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-[#A100FF] p-4">
                <DollarSign className="h-8 w-8 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Estimated Cost</p>
                <p className="text-3xl text-[#1F1F29]">$3.42</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">Cost per Question</p>
              <p className="text-xl text-[#1F1F29]">$0.0122</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={() => navigate("/review-complete")}>
          Back to Review Complete
        </Button>
        <Button
          onClick={() => navigate("/flow")}
          className="bg-[#A100FF] hover:bg-[#8A00DD]"
        >
          View Business Flow
        </Button>
      </div>
    </div>
  );
}
