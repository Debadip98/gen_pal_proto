import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
import {
  CheckCircle2,
  AlertTriangle,
  Download,
  Eye,
  FileSpreadsheet,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui/dialog";

const validationChecks = [
  { id: 1, check: "One workbook only", status: "passed" },
  { id: 2, check: "One sheet only", status: "passed" },
  { id: 3, check: "Sheet name = Sheet1", status: "passed" },
  { id: 4, check: "11 required columns", status: "passed" },
  { id: 5, check: "No extra columns", status: "passed" },
  { id: 6, check: "title serial numbers 1 to 280", status: "passed" },
  { id: 7, check: "ssid present in every row", status: "passed" },
  { id: 8, check: "question_type = QnA", status: "passed" },
  { id: 9, check: "options column blank", status: "passed" },
  { id: 10, check: "reference URLs valid", status: "passed" },
  { id: 11, check: "duplicate check passed", status: "warning" },
];

export function ValidationExport() {
  const navigate = useNavigate();
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [acceptOverride, setAcceptOverride] = useState(false);

  const hasWarnings = validationChecks.some((check) => check.status === "warning");

  const handleDownload = () => {
    if (!acceptOverride && hasWarnings) {
      return;
    }
    setShowSuccessModal(true);
  };

  return (
    <div className="space-y-6 p-6">
      {/* Page Header */}
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">Excel Export Readiness</h2>
        <p className="text-sm text-gray-600">
          Final validation and export of GenPal-ready Excel file.
        </p>
      </div>

      {/* Warning Alert */}
      {hasWarnings && !acceptOverride && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Export Blocked</AlertTitle>
          <AlertDescription>
            Export is blocked because unresolved similar questions remain. Please review
            duplicates or accept manual override to proceed.
          </AlertDescription>
          <div className="mt-4 flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/duplicates")}
              className="border-white text-white hover:bg-red-700"
            >
              Review Duplicates
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAcceptOverride(true)}
              className="border-white text-white hover:bg-red-700"
            >
              Accept Manual Override
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="border-white text-white hover:bg-red-700"
            >
              Re-run Repair
            </Button>
          </div>
        </Alert>
      )}

      {/* Validation Checklist */}
      <Card>
        <CardHeader>
          <CardTitle>Validation Checklist</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {validationChecks.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-lg border p-3"
              >
                <div className="flex items-center gap-3">
                  {item.status === "passed" ? (
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-amber-600" />
                  )}
                  <span className="text-sm text-[#1F1F29]">{item.check}</span>
                </div>
                <Badge
                  variant={item.status === "passed" ? "default" : "outline"}
                  className={
                    item.status === "passed"
                      ? "bg-green-600"
                      : "border-amber-600 text-amber-600"
                  }
                >
                  {item.status === "passed" ? "Passed" : "Warning"}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Export Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Export Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-3">
              <div>
                <p className="text-xs text-gray-500">Output File</p>
                <p className="text-sm text-[#1F1F29] break-words">
                  Microsoft SharePoint Server Development-80002591.xlsx
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Sheet Name</p>
                <p className="text-sm text-[#1F1F29]">Sheet1</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Total Rows</p>
                <p className="text-sm text-[#1F1F29]">280</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Career Levels</p>
                <p className="text-sm text-[#1F1F29]">7</p>
              </div>
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-xs text-gray-500">Questions per Level</p>
                <p className="text-sm text-[#1F1F29]">40</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Duplicate Threshold</p>
                <p className="text-sm text-[#1F1F29]">0.85</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Final Validation</p>
                <Badge
                  variant={hasWarnings && !acceptOverride ? "outline" : "default"}
                  className={
                    hasWarnings && !acceptOverride
                      ? "border-amber-600 text-amber-600"
                      : "bg-green-600"
                  }
                >
                  {hasWarnings && !acceptOverride
                    ? "Warnings Present"
                    : "Passed with Override"}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Excel Format Reference */}
      <Card className="bg-[#F7F7FA]">
        <CardHeader>
          <CardTitle className="text-base">GenPal Excel Format</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-2">
            <FileSpreadsheet className="mt-0.5 h-4 w-4 text-gray-600" />
            <div className="flex-1">
              <p className="text-sm text-[#1F1F29]">Single workbook, single sheet</p>
              <p className="text-xs text-gray-500">
                Sheet name must be exactly "Sheet1"
              </p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <FileSpreadsheet className="mt-0.5 h-4 w-4 text-gray-600" />
            <div className="flex-1">
              <p className="text-sm text-[#1F1F29]">11 required columns in exact order</p>
              <p className="text-xs text-gray-500 font-mono">
                title, ssid, skill, topic, question_type, career_level, complexity, question,
                answer, options, reference_url
              </p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <FileSpreadsheet className="mt-0.5 h-4 w-4 text-gray-600" />
            <div className="flex-1">
              <p className="text-sm text-[#1F1F29]">No metadata sheets or extra columns</p>
              <p className="text-xs text-gray-500">
                GenPal only accepts the standard format
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={() => navigate("/preview")}>
          Back to Preview
        </Button>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => navigate("/duplicates")}>
            <Eye className="mr-2 h-4 w-4" />
            View Duplicate Report
          </Button>
          <Button
            onClick={handleDownload}
            disabled={hasWarnings && !acceptOverride}
            className="bg-[#A100FF] hover:bg-[#8A00DD]"
          >
            <Download className="mr-2 h-4 w-4" />
            Download Excel
          </Button>
        </div>
      </div>

      {/* Success Modal */}
      <Dialog open={showSuccessModal} onOpenChange={setShowSuccessModal}>
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
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">File name:</span>
              <span className="text-[#1F1F29]">
                Microsoft SharePoint Server Development-80002591.xlsx
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Row count:</span>
              <span className="text-[#1F1F29]">280</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Sheet name:</span>
              <span className="text-[#1F1F29]">Sheet1</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Column count:</span>
              <span className="text-[#1F1F29]">11</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Duplicate check status:</span>
              <Badge variant="outline" className="border-amber-600 text-amber-600">
                Manual Override Applied
              </Badge>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => navigate("/preview")}>
              Back to Preview
            </Button>
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
