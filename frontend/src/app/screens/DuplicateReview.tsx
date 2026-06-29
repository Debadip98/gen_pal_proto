import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Checkbox } from "../components/ui/checkbox";
import { Label } from "../components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { CheckCircle2, AlertTriangle, X, RefreshCw, ChevronRight } from "lucide-react";

type DuplicateStatus = "candidate" | "reworked" | "manual-review" | "false-positive";

interface DuplicatePair {
  id: number;
  row1: number;
  row2: number;
  level1: string;
  level2: string;
  complexity1: string;
  complexity2: string;
  similarity: number;
  status: DuplicateStatus;
  similarityLabel?: string;
}

const initialPairs: DuplicatePair[] = [
  { id: 1, row1: 189, row2: 203, level1: "AM", level2: "M", complexity1: "Proficient", complexity2: "Basic", similarity: 1.0, status: "reworked" },
  { id: 2, row1: 189, row2: 218, level1: "AM", level2: "M", complexity1: "Proficient", complexity2: "Advanced", similarity: 1.0, status: "manual-review" },
  { id: 3, row1: 45, row2: 88, level1: "SE", level2: "SSE", complexity1: "Advanced", complexity2: "Basic", similarity: 0.89, status: "false-positive" },
  { id: 4, row1: 112, row2: 156, level1: "SSE", level2: "TL", complexity1: "Proficient", complexity2: "Basic", similarity: 0.92, status: "reworked" },
  { id: 5, row1: 73, row2: 134, level1: "SE", level2: "SSE", complexity1: "Basic", complexity2: "Proficient", similarity: 0.87, status: "false-positive" },
];

export function DuplicateReview() {
  const navigate = useNavigate();
  const [pairs, setPairs] = useState<DuplicatePair[]>(initialPairs);
  const [selectedPairId, setSelectedPairId] = useState<number>(2);
  const [manualOverride, setManualOverride] = useState(false);

  const selectedPair = pairs.find((p) => p.id === selectedPairId) ?? pairs[0];

  const updateStatus = (id: number, status: DuplicateStatus, similarityLabel?: string) => {
    setPairs((prev) =>
      prev.map((p) =>
        p.id === id ? { ...p, status, ...(similarityLabel !== undefined ? { similarityLabel } : {}) } : p
      )
    );
  };

  const getStatusBadge = (pair: DuplicatePair) => {
    switch (pair.status) {
      case "reworked":
        return <Badge className="bg-green-600 whitespace-nowrap"><CheckCircle2 className="mr-1 h-3 w-3" />Reworked</Badge>;
      case "manual-review":
        return <Badge variant="outline" className="border-red-600 text-red-600 whitespace-nowrap">Manual Review Required</Badge>;
      case "false-positive":
        return <Badge variant="outline" className="border-gray-500 text-gray-500 whitespace-nowrap">False Positive</Badge>;
      default:
        return <Badge variant="outline" className="border-amber-600 text-amber-600 whitespace-nowrap">Candidate</Badge>;
    }
  };

  const manualReviewCount = pairs.filter((p) => p.status === "manual-review").length;
  const reworkedCount = pairs.filter((p) => p.status === "reworked").length;

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">Duplicate / Similar Scenario Findings</h2>
        <p className="text-sm text-gray-600">
          Review and manage similar questions detected by embeddings.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-2xl text-[#1F1F29]">34</p>
              <p className="text-xs text-gray-500">Similar Pairs Found</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-2xl text-[#1F1F29]">1.00</p>
              <p className="text-xs text-gray-500">Highest Similarity</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-2xl text-[#1F1F29]">0.85</p>
              <p className="text-xs text-gray-500">Threshold</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-2xl text-[#1F1F29]">{reworkedCount}</p>
              <p className="text-xs text-gray-500">Reworked Rows</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-2xl text-amber-600">{manualReviewCount}</p>
              <p className="text-xs text-gray-500">Manual Review Required</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Table + Drawer layout */}
      <div className="flex gap-6">
        {/* Pairs Table */}
        <div className={selectedPair ? "flex-1 min-w-0" : "w-full"}>
          <Card>
            <CardHeader>
              <CardTitle>Similar Question Pairs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Pair ID</TableHead>
                      <TableHead>Row 1</TableHead>
                      <TableHead>Row 2</TableHead>
                      <TableHead>Career Levels</TableHead>
                      <TableHead>Complexities</TableHead>
                      <TableHead>Similarity</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pairs.map((pair) => (
                      <TableRow
                        key={pair.id}
                        className={`cursor-pointer ${selectedPairId === pair.id ? "bg-[#F7F7FA]" : ""}`}
                        onClick={() => setSelectedPairId(pair.id)}
                      >
                        <TableCell>{pair.id}</TableCell>
                        <TableCell>{pair.row1}</TableCell>
                        <TableCell>{pair.row2}</TableCell>
                        <TableCell>{pair.level1} / {pair.level2}</TableCell>
                        <TableCell>{pair.complexity1} / {pair.complexity2}</TableCell>
                        <TableCell>
                          {pair.similarityLabel ? (
                            <Badge variant="outline" className="border-amber-600 text-amber-600 whitespace-nowrap">
                              Pending recheck
                            </Badge>
                          ) : (
                            <Badge variant={pair.similarity >= 0.95 ? "destructive" : "secondary"}>
                              {pair.similarity.toFixed(2)}
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>{getStatusBadge(pair)}</TableCell>
                        <TableCell>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="gap-1"
                            onClick={(e) => { e.stopPropagation(); setSelectedPairId(pair.id); }}
                          >
                            Review <ChevronRight className="h-3 w-3" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right-side Drawer Panel */}
        {selectedPair && (
          <div className="w-[420px] shrink-0">
            <Card className="sticky top-4 border-2 border-[#A100FF]">
              <CardHeader className="bg-[#F7F7FA]">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">Pair #{selectedPair.id} — Comparison</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant={selectedPair.similarity >= 0.95 ? "destructive" : "secondary"}>
                      {selectedPair.similarityLabel ?? `Similarity: ${selectedPair.similarity.toFixed(2)}`}
                    </Badge>
                    <button
                      onClick={() => setSelectedPairId(0)}
                      className="rounded p-1 hover:bg-[#D9D9E3]"
                    >
                      <X className="h-4 w-4 text-gray-500" />
                    </button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4 pt-4">
                {/* Side-by-side comparison */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2 rounded-lg border p-3">
                    <p className="text-xs text-gray-400">Question 1 — Row {selectedPair.row1}</p>
                    <div>
                      <p className="text-xs text-gray-500">Topic</p>
                      <p className="text-xs text-[#1F1F29]">SharePoint Server Farm Architecture</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Career Level</p>
                      <Badge variant="secondary" className="text-xs">{selectedPair.level1}</Badge>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Complexity</p>
                      <Badge variant="outline" className="text-xs">{selectedPair.complexity1}</Badge>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Question</p>
                      <p className="text-xs text-[#1F1F29]">A junior developer is asked to verify why a SharePoint site collection is not loading after a farm configuration change. What should they check first?</p>
                    </div>
                  </div>
                  <div className="space-y-2 rounded-lg border p-3">
                    <p className="text-xs text-gray-400">Question 2 — Row {selectedPair.row2}</p>
                    <div>
                      <p className="text-xs text-gray-500">Topic</p>
                      <p className="text-xs text-[#1F1F29]">SharePoint Server Farm Architecture</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Career Level</p>
                      <Badge variant="secondary" className="text-xs">{selectedPair.level2}</Badge>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Complexity</p>
                      <Badge variant="outline" className="text-xs">{selectedPair.complexity2}</Badge>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Question</p>
                      <p className="text-xs text-[#1F1F29]">
                        {selectedPair.status === "manual-review"
                          ? "A junior developer is asked to verify why a SharePoint site collection is not loading after a farm configuration change. What should they check first?"
                          : "A developer needs to troubleshoot a SharePoint site that stopped working after maintenance. What diagnostic steps should they follow?"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Verifier decision */}
                <div className="space-y-1">
                  <p className="text-xs text-gray-500">Verifier Decision</p>
                  <div>{getStatusBadge(selectedPair)}</div>
                </div>

                {/* Drawer action buttons */}
                <div className="space-y-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-start"
                    onClick={() => updateStatus(selectedPair.id, "false-positive")}
                  >
                    <CheckCircle2 className="mr-2 h-4 w-4 text-green-600" />
                    Accept as False Positive
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-start border-amber-600 text-amber-700"
                    onClick={() => updateStatus(selectedPair.id, "reworked", "Pending recheck")}
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Rework Question
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-start border-red-600 text-red-600"
                    onClick={() => updateStatus(selectedPair.id, "manual-review")}
                  >
                    <AlertTriangle className="mr-2 h-4 w-4" />
                    Mark Manual Review
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Manual Override Checkbox */}
      <Card className={manualReviewCount > 0 ? "border-amber-400" : ""}>
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Checkbox
              id="manualOverride"
              checked={manualOverride}
              onCheckedChange={(v) => setManualOverride(!!v)}
            />
            <div className="space-y-1">
              <Label htmlFor="manualOverride" className="cursor-pointer text-sm text-[#1F1F29]">
                I confirm remaining similar pairs are acceptable or will be reviewed manually.
              </Label>
              {manualReviewCount > 0 && (
                <p className="text-xs text-amber-600">
                  {manualReviewCount} pair{manualReviewCount > 1 ? "s" : ""} still require manual review. Selecting this override allows export to continue with a warning.
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Navigation Actions */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={() => navigate("/progress")}>
          Back to Progress
        </Button>
        <Button
          onClick={() => navigate("/preview")}
          className="bg-[#A100FF] hover:bg-[#8A00DD]"
        >
          Continue After Review
        </Button>
      </div>
    </div>
  );
}
