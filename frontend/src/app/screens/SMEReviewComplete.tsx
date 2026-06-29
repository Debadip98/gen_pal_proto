import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { CheckCircle2, Download, Bell, AlertTriangle } from "lucide-react";

export function SMEReviewComplete() {
  const navigate = useNavigate();
  const [notified, setNotified] = useState(false);
  const allAccepted = true;

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">Review Complete</h2>
        <p className="text-sm text-gray-600">SME review has concluded. Review the final status before exporting.</p>
      </div>

      {/* Summary metrics */}
      <div className="grid gap-4 md:grid-cols-6">
        {[
          { label: "Total Questions", value: "80", color: "" },
          { label: "Accepted", value: "78", color: "text-green-600" },
          { label: "Rejected", value: "0", color: "text-red-600" },
          { label: "Regenerated", value: "2", color: "text-amber-600" },
          { label: "Pending", value: "0", color: "" },
          { label: "Manual Override Used", value: "No", color: "text-green-600" },
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

      {/* Success / warning state */}
      {allAccepted ? (
        <Card className="border-green-600 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-green-600 p-3">
                <CheckCircle2 className="h-8 w-8 text-white" />
              </div>
              <div>
                <p className="text-lg text-green-800">All questions are approved for export.</p>
                <p className="text-sm text-green-700">The GenPal-ready Excel file is ready for download.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="border-amber-400 bg-amber-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-6 w-6 text-amber-600" />
              <p className="text-sm text-amber-800">Some questions are still pending review.</p>
            </div>
            <div className="mt-4 flex gap-3">
              <Button variant="outline" size="sm" className="border-amber-600 text-amber-700" onClick={() => navigate("/sme-review")}>
                Continue Review
              </Button>
              <Button size="sm" className="bg-amber-600 hover:bg-amber-700 text-white">
                Use Final Override
              </Button>
              <Button variant="outline" size="sm" onClick={() => navigate("/export")}>
                <Download className="mr-2 h-3 w-3" />
                Download Draft Excel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Review summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Review Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              {[
                { label: "Skill", value: "Microsoft SharePoint Server Development" },
                { label: "SSID", value: "80002591" },
                { label: "Total Questions", value: "80" },
                { label: "SME Reviewer", value: "sme@example.com" },
              ].map((item) => (
                <div key={item.label} className="flex justify-between text-sm">
                  <span className="text-gray-500">{item.label}</span>
                  <span className="text-[#1F1F29]">{item.value}</span>
                </div>
              ))}
            </div>
            <div className="space-y-2">
              {[
                { label: "Review Completion", value: "100%" },
                { label: "Regenerated Questions", value: "2" },
                { label: "Duplicate Warnings Resolved", value: "1" },
                { label: "Export Readiness", value: <Badge className="bg-green-600 text-xs">Ready</Badge> },
              ].map((item) => (
                <div key={item.label} className="flex justify-between text-sm items-center">
                  <span className="text-gray-500">{item.label}</span>
                  <span className="text-[#1F1F29]">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notify requestor */}
      {notified ? (
        <Card className="border-green-600 bg-green-50">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <p className="text-sm text-green-800">Requestor notified successfully. They can now download the approved Excel.</p>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {/* Actions */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={() => navigate("/sme-review")}>
          Back to Review Queue
        </Button>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => setNotified(true)}
            disabled={notified}
          >
            <Bell className="mr-2 h-4 w-4" />
            {notified ? "Requestor Notified" : "Notify Requestor"}
          </Button>
          <Button onClick={() => navigate("/export")} className="bg-[#A100FF] hover:bg-[#8A00DD]">
            <Download className="mr-2 h-4 w-4" />
            Download GenPal Import Excel
          </Button>
        </div>
      </div>
    </div>
  );
}
