import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Checkbox } from "../components/ui/checkbox";
import { Slider } from "../components/ui/slider";
import { ArrowRight, RotateCcw, Loader2 } from "lucide-react";
import { api } from "../services/api";
import { useJob } from "../context/JobContext";

const ALL_LEVELS = ["ASE", "SE", "SSE", "TL", "AM", "M", "SM"];
type LevelConfig = { enabled: boolean; count: number };

const defaultLevels: Record<string, LevelConfig> = {
  ASE: { enabled: true, count: 40 }, SE: { enabled: true, count: 40 },
  SSE: { enabled: false, count: 40 }, TL: { enabled: false, count: 40 },
  AM: { enabled: false, count: 40 }, M: { enabled: false, count: 40 },
  SM: { enabled: false, count: 40 },
};

export function LandingPage() {
  const navigate = useNavigate();
  const { setJob } = useJob();
  const [skillName, setSkillName] = useState("Microsoft SharePoint Server Development");
  const [skillId, setSkillId] = useState("80002591");
  const [requestorEmail, setRequestorEmail] = useState("requestor@example.com");
  const [smeEmail, setSmeEmail] = useState("sme@example.com");
  const [topics, setTopics] = useState(
    "SharePoint Server Farm Architecture\nSharePoint Server Object Model\nSharePoint Search Configuration\nSharePoint Security and Permissions"
  );
  const [urls, setUrls] = useState("https://learn.microsoft.com/\nhttps://support.microsoft.com/");
  const [autoFindDocs, setAutoFindDocs] = useState(false);
  const [mode, setMode] = useState<"fixed" | "dynamic">("fixed");
  const [levelConfigs, setLevelConfigs] = useState<Record<string, LevelConfig>>(defaultLevels);
  const [threshold, setThreshold] = useState([0.85]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleLevel = (level: string) =>
    setLevelConfigs((prev) => ({ ...prev, [level]: { ...prev[level], enabled: !prev[level].enabled } }));
  const setCount = (level: string, count: number) =>
    setLevelConfigs((prev) => ({ ...prev, [level]: { ...prev[level], count: Math.max(1, count) } }));

  const selectedLevels = ALL_LEVELS.filter((l) => levelConfigs[l].enabled);
  const totalQuestions = selectedLevels.reduce((acc, l) => acc + levelConfigs[l].count, 0);

  const handleReset = () => {
    setSkillName(""); setSkillId(""); setRequestorEmail(""); setSmeEmail("");
    setTopics(""); setUrls(""); setAutoFindDocs(false); setMode("fixed");
    setLevelConfigs(defaultLevels); setThreshold([0.85]); setError(null);
  };

  const handleGenerate = async () => {
    if (!skillName || selectedLevels.length === 0) {
      setError("Please enter a skill name and select at least one career level.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const career_levels: Record<string, number> = {};
      selectedLevels.forEach((l) => { career_levels[l] = levelConfigs[l].count; });
      const job = await api.createJob({
        skill_name: skillName, skill_id: skillId,
        requestor_email: requestorEmail, sme_email: smeEmail,
        topics: topics.split("\n").map((t) => t.trim()).filter(Boolean),
        reference_urls: urls.split("\n").map((u) => u.trim()).filter(Boolean),
        career_levels, duplicate_threshold: threshold[0], auto_find_docs: autoFindDocs,
      });
      setJob(job.id, job.job_token);
      navigate(autoFindDocs ? "/docs" : "/progress");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create job.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-1">
        <h2 className="text-2xl text-[#1F1F29]">GenPal Question Bank Factory</h2>
        <p className="text-sm text-gray-600">AI-assisted question bank generation with SME review and GenPal-ready Excel export.</p>
      </div>

      <Card>
        <CardContent className="pt-5 pb-5">
          <div className="flex items-center justify-between">
            {["Input", "Generate", "Validate", "SME Review", "Export Excel"].map((step, i) => (
              <div key={step} className="flex items-center gap-2">
                <div className="flex flex-col items-center">
                  <div className={`flex h-9 w-9 items-center justify-center rounded-full text-sm ${i === 0 ? "bg-[#A100FF] text-white" : "bg-[#D9D9E3] text-[#1F1F29]"}`}>{i + 1}</div>
                  <p className={`mt-1.5 text-xs ${i === 0 ? "text-[#A100FF]" : "text-gray-500"}`}>{step}</p>
                </div>
                {i < 4 && <ArrowRight className="h-4 w-4 text-[#D9D9E3] shrink-0 mb-4" />}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Input Form</CardTitle>
              <CardDescription>Enter the required details for question bank generation.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="skillName">Skill Name</Label>
                  <Input id="skillName" value={skillName} onChange={(e) => setSkillName(e.target.value)} placeholder="Microsoft SharePoint Server Development" />
                  <p className="text-xs text-gray-500">Enter the skill name exactly as it should appear in Excel.</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="skillId">Skill ID / SSID</Label>
                  <Input id="skillId" value={skillId} onChange={(e) => setSkillId(e.target.value)} placeholder="80002591" />
                  <p className="text-xs text-gray-500">This value will be repeated in every Excel row.</p>
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="requestorEmail">Requestor Email</Label>
                  <Input id="requestorEmail" type="email" value={requestorEmail} onChange={(e) => setRequestorEmail(e.target.value)} placeholder="requestor@example.com" />
                  <p className="text-xs text-gray-500">Notifications will be sent to this email after SME actions.</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smeEmail">SME Email ID</Label>
                  <Input id="smeEmail" type="email" value={smeEmail} onChange={(e) => setSmeEmail(e.target.value)} placeholder="sme@example.com" />
                  <p className="text-xs text-gray-500">The SME review link will be sent to this email.</p>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="topics">Topic List</Label>
                <Textarea id="topics" value={topics} onChange={(e) => setTopics(e.target.value)} className="min-h-28" placeholder={"SharePoint Server Farm Architecture\nSharePoint Server Object Model"} />
                <p className="text-xs text-gray-500">Paste one topic per line.</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="urls">Reference URL List</Label>
                <Textarea id="urls" value={urls} onChange={(e) => setUrls(e.target.value)} className="min-h-20" placeholder={"https://learn.microsoft.com/\nhttps://support.microsoft.com/"} />
                <p className="text-xs text-gray-500">Paste one reference URL per line.</p>
              </div>
              <div className="flex items-start gap-3 rounded-lg border border-[#D9D9E3] p-4">
                <Checkbox id="autoFindDocs" checked={autoFindDocs} onCheckedChange={(v) => setAutoFindDocs(!!v)} />
                <div>
                  <Label htmlFor="autoFindDocs" className="cursor-pointer text-sm text-[#1F1F29]">Auto-find latest documentation from web based on Skill Name</Label>
                  <p className="mt-1 text-xs text-gray-500">The system will search official/latest docs and suggest additional references.</p>
                </div>
              </div>
              <div className="space-y-3">
                <Label>Generation Mode</Label>
                <div className="flex rounded-lg border border-[#D9D9E3] overflow-hidden w-fit">
                  <button onClick={() => setMode("fixed")} className={`px-5 py-2 text-sm transition-colors ${mode === "fixed" ? "bg-[#A100FF] text-white" : "bg-white text-gray-600 hover:bg-[#F7F7FA]"}`}>Fixed GenPal Count</button>
                  <button onClick={() => setMode("dynamic")} className={`px-5 py-2 text-sm transition-colors ${mode === "dynamic" ? "bg-[#A100FF] text-white" : "bg-white text-gray-600 hover:bg-[#F7F7FA]"}`}>Dynamic Count</button>
                </div>
                <p className="text-xs text-gray-500">{mode === "fixed" ? "Fixed GenPal Count: 40 questions per selected career level." : "Dynamic Count: Enter a custom question count per career level."}</p>
              </div>
              <div className="space-y-2">
                <Label>Career Level Configuration</Label>
                <div className="overflow-auto rounded-lg border border-[#D9D9E3]">
                  <table className="w-full text-sm">
                    <thead className="bg-[#F7F7FA]">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs text-gray-500">Enabled</th>
                        <th className="px-4 py-2 text-left text-xs text-gray-500">Career Level</th>
                        <th className="px-4 py-2 text-left text-xs text-gray-500">Question Count</th>
                        <th className="px-4 py-2 text-left text-xs text-gray-500">Complexity Distribution</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#D9D9E3]">
                      {ALL_LEVELS.map((level) => {
                        const cfg = levelConfigs[level];
                        const basic = Math.round(cfg.count * 0.33);
                        const prof = Math.round(cfg.count * 0.34);
                        const adv = cfg.count - basic - prof;
                        return (
                          <tr key={level} className={cfg.enabled ? "" : "opacity-50"}>
                            <td className="px-4 py-2"><Checkbox checked={cfg.enabled} onCheckedChange={() => toggleLevel(level)} /></td>
                            <td className="px-4 py-2"><Badge variant={cfg.enabled ? "default" : "outline"} className={cfg.enabled ? "bg-[#A100FF]" : ""}>{level}</Badge></td>
                            <td className="px-4 py-2">
                              {mode === "dynamic" && cfg.enabled
                                ? <Input type="number" value={cfg.count} onChange={(e) => setCount(level, parseInt(e.target.value) || 0)} className="h-7 w-20 text-sm" />
                                : <span className="text-[#1F1F29]">{cfg.count}</span>}
                            </td>
                            <td className="px-4 py-2"><span className="text-xs text-gray-500">Basic {basic} · Proficient {prof} · Advanced {adv}</span></td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Duplicate Similarity Threshold</Label>
                  <span className="text-sm text-[#1F1F29]">{threshold[0].toFixed(2)}</span>
                </div>
                <Slider value={threshold} onValueChange={setThreshold} min={0.5} max={1.0} step={0.05} className="[&_[role=slider]]:bg-[#A100FF] [&_[role=slider]]:border-[#A100FF]" />
                <p className="text-xs text-gray-500">Questions above this similarity score are flagged for duplicate review.</p>
              </div>
              <div className="flex gap-3 pt-2">
                <Button onClick={handleGenerate} disabled={loading} className="flex-1 bg-[#A100FF] hover:bg-[#8A00DD]">
                  {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Creating Job…</> : "Generate Question Bank"}
                </Button>
                <Button variant="outline" onClick={handleReset} disabled={loading}>
                  <RotateCcw className="mr-2 h-4 w-4" />Reset Form
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Expected Output Summary</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div><p className="text-xs text-gray-500">Skill Name</p><p className="text-sm text-[#1F1F29]">{skillName || "—"}</p></div>
              <div><p className="text-xs text-gray-500">Skill ID / SSID</p><p className="text-sm text-[#1F1F29]">{skillId || "—"}</p></div>
              <div><p className="text-xs text-gray-500">Requestor Email</p><p className="text-sm text-[#1F1F29] break-all">{requestorEmail || "—"}</p></div>
              <div><p className="text-xs text-gray-500">SME Email</p><p className="text-sm text-[#1F1F29] break-all">{smeEmail || "—"}</p></div>
              <div>
                <p className="text-xs text-gray-500">Selected Career Levels</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {selectedLevels.length ? selectedLevels.map((l) => <Badge key={l} variant="secondary" className="text-xs">{l}</Badge>) : <span className="text-xs text-gray-400">None selected</span>}
                </div>
              </div>
              <div><p className="text-xs text-gray-500">Total Expected Questions</p><p className="text-sm text-[#1F1F29]">{totalQuestions}</p></div>
              <div className="border-t pt-3">
                <p className="text-xs text-gray-500">Output File Name</p>
                <p className="text-sm text-[#1F1F29] break-words">{skillName && skillId ? `${skillName}-${skillId}.xlsx` : "—"}</p>
              </div>
              <div className="space-y-1.5 rounded-lg bg-[#F7F7FA] p-3">
                <div className="flex justify-between text-xs"><span className="text-gray-500">Sheet name:</span><span className="text-[#1F1F29]">Sheet1</span></div>
                <div className="flex justify-between text-xs"><span className="text-gray-500">Columns:</span><span className="text-[#1F1F29]">11</span></div>
                <div className="flex justify-between text-xs"><span className="text-gray-500">Threshold:</span><span className="text-[#1F1F29]">{threshold[0].toFixed(2)}</span></div>
              </div>
              {autoFindDocs && (
                <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
                  <p className="text-xs text-blue-800">Auto-documentation discovery enabled. You will be directed to the Docs Discovery screen first.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
