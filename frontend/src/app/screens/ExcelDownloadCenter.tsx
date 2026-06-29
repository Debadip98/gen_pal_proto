import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogDescription,
} from "../components/ui/dialog";
import { CheckCircle2, Download, AlertTriangle, FileSpreadsheet } from "lucide-react";

const validationChecks = [
  { check: "One workbook only", status: "passed" },
  { check: "One sheet only (Sheet1)", status: "passed" },
  { check: "11 required columns", status: "passed" },
  { check: "title serial numbers 1 to 280", status: "passed" },
  { check: "ssid present in every row", status: "passed" },
  { check: "question_type = QnA", status: "passed" },
  { check: "options column blank", status: "passed" },
  { check: "No internal review metadata exported", status: "passed" },
];

export function ExcelDownloadCenter() {
  const navigate = useNavigate();
  const [showModal, setShowModal] = useState(false);
  const [downloadType, setDownloadType] = useState<"draft" | "approved">("approved");

  const handleDownload = (type: "draft" | "approved") => {
    setDownloadType(type);
    setShowModal(true);
  };

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">Excel Download Center</h2>
        <p className="text-sm text-gray-600">Download the GenPal-ready Excel file in draft or approved form.</p>
      </div>

      {/* Two download cards */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Draft */}
        <Card className="border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FileSpreadsheet className="h-5 w-5 text-gray-600" />
              Current Draft Excel
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-600">Available once generated rows exist. May include questions not fully accepted by SME.</p>
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                <p className="text-xs text-amber-800">Some questions may still be pending SME review. This file includes all generated rows regardless of review status.</p>
              </div>
            </div>
            <div className="space-y-1 text-xs text-gray-500">
              <div className="flex justify-between">
                <span>File name</span>
                <span className="text-[#1F1F29]">Microsoft SharePoint Server Development-80002591.xlsx</span>
              </div>
              <div className="flex justify-between">
                <span>Rows</span>
                <span className="text-[#1F1F29]">80</span>
              </div>
              <div className="flex justify-between">
                <span>Status</span>
                <Badge variant="outline" className="border-amber-600 text-amber-600 text-xs">Draft</Badge>
              </div>
            </div>
            <Button variant="outline" className="w-full" onClick={() => handleDownload("draft")}>
              <Download className="mr-2 h-4 w-4" />
              Download Draft Excel
            </Button>
          </CardContent>
        </Card>

        {/* Approved */}
        <Card className="border-2 border-green-600">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FileSpreadsheet className="h-5 w-5 text-green-600" />
              Approved GenPal Excel
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-600">Available after all questions are accepted or final override is confirmed.</p>
            <div className="rounded-lg border border-green-200 bg-green-50 p-3">
              <div className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                <p className="text-xs text-green-800">All 80 questions have been reviewed and approved by the SME. This file is ready for GenPal import.</p>
              </div>
            </div>
            <div className="space-y-1 text-xs text-gray-500">
              <div className="flex justify-between">
                <span>File name</span>
                <span className="text-[#1F1F29]">Microsoft SharePoint Server Development-80002591.xlsx</span>
              </div>
              <div className="flex justify-between">
                <span>Rows</span>
                <span className="text-[#1F1F29]">80</span>
              </div>
              <div className="flex justify-between">
                <span>Status</span>
                <Badge className="bg-green-600 text-xs">Approved</Badge>
              </div>
            </div>
            <Button className="w-full bg-green-600 hover:bg-green-700" onClick={() => handleDownload("approved")}>
              <Download className="mr-2 h-4 w-4" />
              Download Approved Excel
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Excel validation checklist */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Excel Validation Checklist</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-2">
            {validationChecks.map((item) => (
              <div key={item.check} className="flex items-center gap-3 rounded-lg border p-3">
                <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                <span className="text-sm text-[#1F1F29]">{item.check}</span>
                <Badge className="ml-auto bg-green-600 text-xs">Passed</Badge>
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-lg bg-[#F7F7FA] p-3">
            <p className="text-xs text-gray-500 font-mono">
              Review metadata (review_status, sme_feedback, llm_suggestion) is shown in the UI only and is NOT exported to Excel.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* GenPal column reference */}
      <Card className="bg-[#F7F7FA]">
        <CardHeader>
          <CardTitle className="text-base">GenPal Excel Columns (Exact Order)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {["title","ssid","skill","topic","question_type","career_level","complexity","question","answer","options","reference_url"].map((col) => (
              <Badge key={col} variant="secondary" className="font-mono text-xs">{col}</Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={() => navigate("/review-complete")}>
          Back to Review Complete
        </Button>
        <Button onClick={() => navigate("/cost")} variant="outline">
          View Cost Summary
        </Button>
      </div>

      {/* Success Modal */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
              Excel Export Ready
            </DialogTitle>
            <DialogDescription>
              The GenPal-ready Excel file has been generated successfully.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-4">
            {[
              { label: "File name", value: "Microsoft SharePoint Server Development-80002591.xlsx" },
              { label: "Row count", value: "80" },
              { label: "Sheet name", value: "Sheet1" },
              { label: "Column count", value: "11" },
            ].map((item) => (
              <div key={item.label} className="flex justify-between text-sm">
                <span className="text-gray-500">{item.label}:</span>
                <span className="text-[#1F1F29]">{item.value}</span>
              </div>
            ))}
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Duplicate check status:</span>
              <Badge className="bg-green-600 text-xs">Passed</Badge>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">SME review status:</span>
              <Badge className={downloadType === "approved" ? "bg-green-600 text-xs" : "border-amber-600 text-amber-600 text-xs"} variant={downloadType === "approved" ? "default" : "outline"}>
                {downloadType === "approved" ? "Approved" : "Draft"}
              </Badge>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowModal(false)}>Close</Button>
            <Button className="bg-[#A100FF] hover:bg-[#8A00DD]">
              <Download className="mr-2 h-4 w-4" />
              Download Excel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
