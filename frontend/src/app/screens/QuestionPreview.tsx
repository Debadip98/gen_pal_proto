import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { Search, CheckCircle2, AlertTriangle } from "lucide-react";
import { ScrollArea } from "../components/ui/scroll-area";

const sampleQuestions = [
  {
    title: 1,
    ssid: "80002591",
    skill: "Microsoft SharePoint Server Development",
    topic: "SharePoint Server Farm Architecture",
    question_type: "QnA",
    career_level: "ASE",
    complexity: "Basic",
    question:
      "A junior developer is asked to verify why a SharePoint site collection is not loading after a recent farm configuration change. What should they check first?",
    answer:
      "They should first confirm the web application status, application pool health, and farm service availability using Central Administration and PowerShell commands.",
    options: "",
    reference_url: "https://learn.microsoft.com/",
  },
  {
    title: 2,
    ssid: "80002591",
    skill: "Microsoft SharePoint Server Development",
    topic: "SharePoint Server Object Model",
    question_type: "QnA",
    career_level: "ASE",
    complexity: "Proficient",
    question:
      "An ASE needs to retrieve all items from a SharePoint list programmatically. Which object model approach is recommended for a server-side solution?",
    answer:
      "Use the SPList object via the SharePoint Server Object Model (SSOM) with SPQuery for efficient filtering and retrieval of list items.",
    options: "",
    reference_url: "https://learn.microsoft.com/",
  },
  {
    title: 3,
    ssid: "80002591",
    skill: "Microsoft SharePoint Server Development",
    topic: "SharePoint Search Configuration",
    question_type: "QnA",
    career_level: "SE",
    complexity: "Advanced",
    question:
      "A software engineer is troubleshooting search results that are not showing recently updated documents. What search service configuration should they review?",
    answer:
      "Review the crawl schedules, content sources configuration, and verify the incremental crawl status. Check if the content processing pipeline is functioning correctly.",
    options: "",
    reference_url: "https://learn.microsoft.com/",
  },
  {
    title: 4,
    ssid: "80002591",
    skill: "Microsoft SharePoint Server Development",
    topic: "SharePoint Security and Permissions",
    question_type: "QnA",
    career_level: "SSE",
    complexity: "Proficient",
    question:
      "A senior engineer needs to implement custom permission levels for a site collection. What is the correct approach?",
    answer:
      "Create a custom permission level via Site Settings > Site Permissions > Permission Levels, selecting appropriate base permissions and assigning it to SharePoint groups or users.",
    options: "",
    reference_url: "https://support.microsoft.com/",
  },
];

export function QuestionPreview() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState("");
  const [careerFilter, setCareerFilter] = useState("all");
  const [complexityFilter, setComplexityFilter] = useState("all");

  return (
    <div className="space-y-6 p-6">
      {/* Page Header */}
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">Generated Question Bank Preview</h2>
        <p className="text-sm text-gray-600">
          Review all generated questions in GenPal Excel format.
        </p>
      </div>

      {/* Validation Badges */}
      <div className="flex flex-wrap gap-2">
        <Badge className="bg-green-600">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Schema Valid
        </Badge>
        <Badge className="bg-green-600">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Sheet1 Ready
        </Badge>
        <Badge className="bg-green-600">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          11 Columns
        </Badge>
        <Badge className="bg-green-600">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          No Extra Fields
        </Badge>
        <Badge className="bg-green-600">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          SSID Present
        </Badge>
        <Badge className="bg-green-600">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Title Serial Numbering
        </Badge>
        <Badge variant="outline" className="border-amber-600 text-amber-600">
          <AlertTriangle className="mr-1 h-3 w-3" />
          Manual Review Required (2)
        </Badge>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <Label htmlFor="search">Search Question Text</Label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="search"
                  placeholder="Search questions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="career">Career Level</Label>
              <Select value={careerFilter} onValueChange={setCareerFilter}>
                <SelectTrigger id="career">
                  <SelectValue placeholder="All levels" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All levels</SelectItem>
                  <SelectItem value="ASE">ASE</SelectItem>
                  <SelectItem value="SE">SE</SelectItem>
                  <SelectItem value="SSE">SSE</SelectItem>
                  <SelectItem value="TL">TL</SelectItem>
                  <SelectItem value="AM">AM</SelectItem>
                  <SelectItem value="M">M</SelectItem>
                  <SelectItem value="SM">SM</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="complexity">Complexity</Label>
              <Select value={complexityFilter} onValueChange={setComplexityFilter}>
                <SelectTrigger id="complexity">
                  <SelectValue placeholder="All complexities" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All complexities</SelectItem>
                  <SelectItem value="Basic">Basic</SelectItem>
                  <SelectItem value="Proficient">Proficient</SelectItem>
                  <SelectItem value="Advanced">Advanced</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  setSearchTerm("");
                  setCareerFilter("all");
                  setComplexityFilter("all");
                }}
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Question Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Question Bank Table</CardTitle>
            <Badge variant="secondary" className="text-base">
              280 rows generated
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px] w-full">
            <div className="overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="min-w-[80px]">title</TableHead>
                    <TableHead className="min-w-[100px]">ssid</TableHead>
                    <TableHead className="min-w-[200px]">skill</TableHead>
                    <TableHead className="min-w-[200px]">topic</TableHead>
                    <TableHead className="min-w-[120px]">question_type</TableHead>
                    <TableHead className="min-w-[120px]">career_level</TableHead>
                    <TableHead className="min-w-[120px]">complexity</TableHead>
                    <TableHead className="min-w-[400px]">question</TableHead>
                    <TableHead className="min-w-[400px]">answer</TableHead>
                    <TableHead className="min-w-[100px]">options</TableHead>
                    <TableHead className="min-w-[200px]">reference_url</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sampleQuestions.map((row) => (
                    <TableRow key={row.title}>
                      <TableCell>{row.title}</TableCell>
                      <TableCell>{row.ssid}</TableCell>
                      <TableCell>{row.skill}</TableCell>
                      <TableCell>{row.topic}</TableCell>
                      <TableCell>
                        <Badge variant="secondary">{row.question_type}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{row.career_level}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{row.complexity}</Badge>
                      </TableCell>
                      <TableCell className="max-w-[400px]">
                        <p className="line-clamp-3 text-xs">{row.question}</p>
                      </TableCell>
                      <TableCell className="max-w-[400px]">
                        <p className="line-clamp-3 text-xs">{row.answer}</p>
                      </TableCell>
                      <TableCell className="text-xs text-gray-400">blank</TableCell>
                      <TableCell className="text-xs text-blue-600 hover:underline">
                        {row.reference_url}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Column Reference */}
      <Card className="bg-[#F7F7FA]">
        <CardHeader>
          <CardTitle className="text-base">GenPal Column Reference</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {[
              "title",
              "ssid",
              "skill",
              "topic",
              "question_type",
              "career_level",
              "complexity",
              "question",
              "answer",
              "options",
              "reference_url",
            ].map((col) => (
              <Badge key={col} variant="secondary" className="font-mono text-xs">
                {col}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Navigation Actions */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={() => navigate("/duplicates")}>
          Back to Duplicates
        </Button>
        <Button
          onClick={() => navigate("/export")}
          className="bg-[#A100FF] hover:bg-[#8A00DD]"
        >
          Continue to Export
        </Button>
      </div>
    </div>
  );
}
