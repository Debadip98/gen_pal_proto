import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Checkbox } from "../components/ui/checkbox";
import { ExternalLink, FileText } from "lucide-react";

const tabKeys = ["Manual URLs", "Auto-Discovered Docs", "Uploaded Docs", "Used Context"] as const;
type Tab = typeof tabKeys[number];

const docs = [
  { id: 1, title: "Microsoft Learn SharePoint Docs", url: "https://learn.microsoft.com/sharepoint/", type: "Official", relevance: "High", summary: "Comprehensive SharePoint Server documentation.", selected: true },
  { id: 2, title: "SharePoint Developer Reference", url: "https://learn.microsoft.com/sharepoint/dev/", type: "Official", relevance: "High", summary: "Developer API and object model reference.", selected: true },
  { id: 3, title: "Microsoft Support SharePoint", url: "https://support.microsoft.com/sharepoint", type: "Support", relevance: "Medium", summary: "Troubleshooting articles for SharePoint Server.", selected: false },
];

export function DocCheckPanel() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<Tab>("Manual URLs");
  const [docList, setDocList] = useState(docs);

  const toggle = (id: number) => setDocList((prev) => prev.map((d) => d.id === id ? { ...d, selected: !d.selected } : d));

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">Documentation Context and Alignment</h2>
        <p className="text-sm text-gray-600">Review how questions are checked against reference documentation.</p>
      </div>

      {/* Tabs */}
      <div className="flex rounded-lg border border-[#D9D9E3] overflow-hidden w-fit">
        {tabKeys.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm transition-colors ${activeTab === tab ? "bg-[#A100FF] text-white" : "bg-white text-gray-600 hover:bg-[#F7F7FA]"}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Document list */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{activeTab}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#F7F7FA]">
                <tr>
                  <th className="px-4 py-2 text-left text-xs text-gray-500">Select</th>
                  <th className="px-4 py-2 text-left text-xs text-gray-500">Title</th>
                  <th className="px-4 py-2 text-left text-xs text-gray-500">Source URL</th>
                  <th className="px-4 py-2 text-left text-xs text-gray-500">Source Type</th>
                  <th className="px-4 py-2 text-left text-xs text-gray-500">Relevance</th>
                  <th className="px-4 py-2 text-left text-xs text-gray-500">Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D9D9E3]">
                {docList.map((doc) => (
                  <tr key={doc.id} className={!doc.selected ? "opacity-60" : ""}>
                    <td className="px-4 py-3">
                      <Checkbox checked={doc.selected} onCheckedChange={() => toggle(doc.id)} />
                    </td>
                    <td className="px-4 py-3 text-xs text-[#1F1F29] max-w-[160px]">
                      <div className="flex items-center gap-1">
                        <FileText className="h-3 w-3 text-gray-400 shrink-0" />
                        <span>{doc.title}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <a href="#" className="flex items-center gap-1 text-xs text-blue-600 hover:underline">
                        <ExternalLink className="h-3 w-3 shrink-0" />
                        <span className="max-w-[160px] truncate">{doc.url}</span>
                      </a>
                    </td>
                    <td className="px-4 py-3"><Badge variant="outline" className="text-xs">{doc.type}</Badge></td>
                    <td className="px-4 py-3">
                      {doc.relevance === "High"
                        ? <Badge className="bg-green-600 text-xs">High</Badge>
                        : <Badge variant="outline" className="border-amber-600 text-amber-600 text-xs">Medium</Badge>}
                    </td>
                    <td className="px-4 py-3 max-w-[200px]">
                      <p className="text-xs text-gray-500 line-clamp-2">{doc.summary}</p>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Question doc alignment card */}
      <Card className="border-2 border-[#A100FF]">
        <CardHeader>
          <CardTitle className="text-base">Question Documentation Alignment</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-xs text-gray-500">Current Question</p>
            <p className="text-sm text-[#1F1F29] mt-1">A senior SharePoint engineer is tasked with designing a governance policy for a department site collection, requiring role-based access with restricted download permissions for contractors...</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs text-gray-500">Reference Source Used</p>
              <p className="text-sm text-blue-600 mt-1">learn.microsoft.com/sharepoint/</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Alignment Status</p>
              <Badge className="mt-1 bg-green-600">ALIGNED</Badge>
            </div>
          </div>
          <div className="rounded-lg bg-green-50 border border-green-200 p-3">
            <p className="text-xs text-green-800">The regenerated question is aligned with the selected Microsoft SharePoint administration documentation. The governance and contractor scenario is supported by the permission level documentation.</p>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={() => navigate("/regenerate")}>
          Back to Rework
        </Button>
        <Button onClick={() => navigate("/regenerate")} className="bg-[#A100FF] hover:bg-[#8A00DD]">
          Use Selected Docs for Rework
        </Button>
      </div>
    </div>
  );
}
