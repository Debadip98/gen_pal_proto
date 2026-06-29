import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Checkbox } from "../components/ui/checkbox";
import { Alert, AlertDescription } from "../components/ui/alert";
import { Search, AlertTriangle, CheckCircle2, ExternalLink, Loader2 } from "lucide-react";

const discoveredDocs = [
  { id: 1, title: "Microsoft Learn SharePoint Docs", domain: "learn.microsoft.com", url: "https://learn.microsoft.com/sharepoint/", relevance: "High", type: "Official", summary: "Comprehensive SharePoint Server documentation including installation, configuration, and administration.", selected: true },
  { id: 2, title: "SharePoint Server Development Guide", domain: "learn.microsoft.com", url: "https://learn.microsoft.com/sharepoint/dev/", relevance: "High", type: "Official", summary: "Developer reference for SharePoint Server APIs, object model, and solution development.", selected: true },
  { id: 3, title: "Microsoft Support SharePoint", domain: "support.microsoft.com", url: "https://support.microsoft.com/sharepoint", relevance: "High", type: "Support", summary: "Troubleshooting articles and how-to guides for SharePoint Server deployments.", selected: true },
  { id: 4, title: "SharePoint Community Blog", domain: "techcommunity.microsoft.com", url: "https://techcommunity.microsoft.com/sharepoint", relevance: "Medium", type: "Community", summary: "Technical community articles on SharePoint patterns and practices.", selected: false },
  { id: 5, title: "SharePoint GitHub Samples", domain: "github.com/pnp", url: "https://github.com/pnp/sp-dev-docs", relevance: "Medium", type: "Community", summary: "Open-source patterns and practices code samples for SharePoint development.", selected: false },
];

const relevanceBadge = (r: string) => {
  if (r === "High") return <Badge className="bg-green-600 text-xs">High</Badge>;
  if (r === "Medium") return <Badge variant="outline" className="border-amber-600 text-amber-600 text-xs">Medium</Badge>;
  return <Badge variant="secondary" className="text-xs">Low</Badge>;
};

export function DocsDiscovery() {
  const navigate = useNavigate();
  const [docs, setDocs] = useState(discoveredDocs);

  const toggle = (id: number) => {
    setDocs((prev) => prev.map((d) => d.id === id ? { ...d, selected: !d.selected } : d));
  };

  const selectedCount = docs.filter((d) => d.selected).length;
  const manualCount = 2;

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">Documentation Discovery</h2>
        <p className="text-sm text-gray-600">
          Review and select documentation sources for question generation.
        </p>
      </div>

      {/* Status banner */}
      <div className="flex items-center gap-3 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3">
        <Loader2 className="h-4 w-4 animate-spin text-blue-600 shrink-0" />
        <p className="text-sm text-blue-800">
          Searching latest official documentation for <strong>Microsoft SharePoint Server Development</strong>…
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-5">
            <div className="text-center">
              <p className="text-2xl text-[#1F1F29]">{manualCount}</p>
              <p className="text-xs text-gray-500">Manual URLs Provided</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <div className="text-center">
              <p className="text-2xl text-[#1F1F29]">{docs.length}</p>
              <p className="text-xs text-gray-500">Auto-Discovered URLs</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <div className="text-center">
              <p className="text-2xl text-[#A100FF]">{selectedCount + manualCount}</p>
              <p className="text-xs text-gray-500">Selected for Generation</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <div className="text-center">
              <Badge className="bg-green-600">Ready</Badge>
              <p className="mt-1 text-xs text-gray-500">Documentation Status</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Manual URLs */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Manual URLs Provided</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {["https://learn.microsoft.com/", "https://support.microsoft.com/"].map((url) => (
              <div key={url} className="flex items-center justify-between rounded-lg border bg-[#F7F7FA] px-4 py-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm text-blue-600">{url}</span>
                </div>
                <Badge className="bg-green-600 text-xs">Always Used</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Discovered docs table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5 text-[#A100FF]" />
              Auto-Discovered Documentation
            </CardTitle>
            <p className="text-xs text-gray-500">{selectedCount} of {docs.length} selected</p>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#F7F7FA]">
                <tr>
                  <th className="px-4 py-2 text-left text-xs text-gray-500">Use</th>
                  <th className="px-4 py-2 text-left text-xs text-gray-500">Source Title</th>
                  <th className="px-4 py-2 text-left text-xs text-gray-500">Domain</th>
                  <th className="px-4 py-2 text-left text-xs text-gray-500">Source Type</th>
                  <th className="px-4 py-2 text-left text-xs text-gray-500">Relevance</th>
                  <th className="px-4 py-2 text-left text-xs text-gray-500">Summary</th>
                  <th className="px-4 py-2 text-left text-xs text-gray-500">URL</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D9D9E3]">
                {docs.map((doc) => (
                  <tr key={doc.id} className={doc.selected ? "" : "opacity-60"}>
                    <td className="px-4 py-3">
                      <Checkbox checked={doc.selected} onCheckedChange={() => toggle(doc.id)} />
                    </td>
                    <td className="px-4 py-3 max-w-[160px]">
                      <p className="text-xs text-[#1F1F29] font-medium">{doc.title}</p>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">{doc.domain}</td>
                    <td className="px-4 py-3">
                      <Badge variant="outline" className="text-xs">{doc.type}</Badge>
                    </td>
                    <td className="px-4 py-3">{relevanceBadge(doc.relevance)}</td>
                    <td className="px-4 py-3 max-w-[240px]">
                      <p className="text-xs text-gray-500 line-clamp-2">{doc.summary}</p>
                    </td>
                    <td className="px-4 py-3">
                      <a href="#" className="flex items-center gap-1 text-xs text-blue-600 hover:underline">
                        <ExternalLink className="h-3 w-3" />
                        Open
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Warning state */}
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription className="text-xs">
          Web search uses live APIs. If unavailable, only manually provided URLs will be used. You can continue with manually provided URLs at any time.
        </AlertDescription>
      </Alert>

      {/* Actions */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={() => navigate("/")}>
          Back to Input
        </Button>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => navigate("/progress")}>
            Use Selected Docs
          </Button>
          <Button onClick={() => navigate("/progress")} className="bg-[#A100FF] hover:bg-[#8A00DD]">
            Continue to Generation
          </Button>
        </div>
      </div>
    </div>
  );
}
