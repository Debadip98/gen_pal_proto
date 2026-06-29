import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import { Alert, AlertDescription } from "../components/ui/alert";
import { RefreshCw, CheckCircle2, AlertTriangle, Loader2 } from "lucide-react";

const preservedFields = [
  { label: "title", value: "4" },
  { label: "ssid", value: "80002591" },
  { label: "skill", value: "Microsoft SharePoint Server Development" },
  { label: "topic", value: "SharePoint Security and Permissions" },
  { label: "question_type", value: "QnA" },
  { label: "career_level", value: "SSE" },
  { label: "complexity", value: "Proficient" },
  { label: "reference_url", value: "https://learn.microsoft.com/" },
];

const validationBadges = [
  "Same topic preserved",
  "Career level preserved",
  "Complexity preserved",
  "Reference URL preserved",
  "Documentation alignment checked",
  "Not similar to previous version",
  "Duplicate check completed",
];

export function RegenerateQuestion() {
  const navigate = useNavigate();
  const [instruction, setInstruction] = useState(
    "Consider regenerating with a deployment or governance scenario to differentiate from Q2."
  );
  const [regenerating, setRegenerating] = useState(false);
  const [done, setDone] = useState(false);

  const handleRegenerate = () => {
    setRegenerating(true);
    setTimeout(() => {
      setRegenerating(false);
      setDone(true);
    }, 1800);
  };

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">Regenerate Question</h2>
        <p className="text-sm text-gray-600">Only this question will be reworked. All other questions remain unchanged.</p>
      </div>

      {/* Warning banner */}
      <Alert className="border-blue-200 bg-blue-50">
        <AlertTriangle className="h-4 w-4 text-blue-600" />
        <AlertDescription className="text-blue-800 text-sm">
          Only this question will be reworked. Other questions will not be changed.
        </AlertDescription>
      </Alert>

      {/* Preserved fields */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Preserved Fields</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-4">
            {preservedFields.map((f) => (
              <div key={f.label} className="rounded-lg bg-[#F7F7FA] px-3 py-2">
                <p className="text-[10px] text-gray-500 font-mono">{f.label}</p>
                <p className="mt-0.5 text-xs text-[#1F1F29] break-words">{f.value}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Current Q&A */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Current Question and Answer</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-xs text-gray-500 mb-1">Question</p>
            <p className="text-sm text-[#1F1F29]">A senior engineer needs to implement custom permission levels for a site collection that meets compliance requirements while restricting document export capabilities. What is the most appropriate approach?</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Answer</p>
            <p className="text-sm text-[#1F1F29]">Create a custom permission level via Site Settings → Site Permissions → Permission Levels. Select appropriate base permissions, explicitly deny the "Use Remote Interfaces" and "Use Client Integration Features" to restrict export.</p>
          </div>
        </CardContent>
      </Card>

      {/* Instruction box */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Regeneration Instruction</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            className="min-h-20"
          />
          <p className="text-xs text-gray-500">Pre-filled from SME feedback or LLM suggestion. Edit as needed.</p>
          {!done && (
            <Button
              onClick={handleRegenerate}
              disabled={regenerating}
              className="bg-[#A100FF] hover:bg-[#8A00DD]"
            >
              {regenerating ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Regenerating…</>
              ) : (
                <><RefreshCw className="mr-2 h-4 w-4" />Regenerate This Question</>
              )}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Side-by-side comparison after regeneration */}
      {done && (
        <>
          <div className="grid gap-6 md:grid-cols-2">
            <Card className="border-2 border-red-200">
              <CardHeader className="bg-red-50">
                <CardTitle className="text-sm text-red-800">Original Question</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 pt-4">
                <div>
                  <p className="text-xs text-gray-500">Question</p>
                  <p className="text-xs text-[#1F1F29]">A senior engineer needs to implement custom permission levels for a site collection that meets compliance requirements while restricting document export capabilities. What is the most appropriate approach?</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Answer</p>
                  <p className="text-xs text-[#1F1F29]">Create a custom permission level via Site Settings → Site Permissions → Permission Levels. Select appropriate base permissions, explicitly deny the "Use Remote Interfaces" and "Use Client Integration Features" to restrict export.</p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-2 border-green-600">
              <CardHeader className="bg-green-50">
                <CardTitle className="text-sm text-green-800">Regenerated Question</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 pt-4">
                <div>
                  <p className="text-xs text-gray-500">Question</p>
                  <p className="text-xs text-[#1F1F29]">A senior SharePoint engineer is tasked with designing a governance policy for a department site collection, requiring role-based access with restricted download permissions for contractors. How should they configure SharePoint permission inheritance and custom levels?</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Answer</p>
                  <p className="text-xs text-[#1F1F29]">Break permission inheritance at the site collection level, create a custom "Contractor View" permission level excluding "Use Remote Interfaces" and download permissions. Assign contractor accounts to a dedicated SharePoint group with this custom level.</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Validation badges */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Validation Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {validationBadges.map((b) => (
                  <Badge key={b} className="bg-green-600 text-xs">
                    <CheckCircle2 className="mr-1 h-3 w-3" />{b}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* SME decision */}
          <div className="flex gap-3">
            <Button
              className="bg-green-600 hover:bg-green-700"
              onClick={() => navigate("/version-compare")}
            >
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Accept Change
            </Button>
            <Button
              variant="outline"
              className="border-red-600 text-red-600"
              onClick={() => navigate("/sme-question")}
            >
              Reject Change
            </Button>
            <Button
              variant="outline"
              className="border-amber-600 text-amber-700"
              onClick={() => setDone(false)}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Regenerate Again
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
