import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Progress } from "../components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Bell, CheckCircle2, Download, AlertTriangle } from "lucide-react";
import { api, type Question, type Notification } from "../services/api";
import { useJob } from "../context/JobContext";

const statusBadge = (s: string) => {
  switch (s) {
    case "accepted": return <Badge className="bg-green-600 text-xs">Accepted</Badge>;
    case "rejected": return <Badge variant="outline" className="border-red-600 text-red-600 text-xs">Rejected</Badge>;
    case "pending-approval": return <Badge variant="outline" className="border-amber-600 text-amber-600 text-xs">Pending Approval</Badge>;
    case "pending": return <Badge variant="secondary" className="text-xs">Pending</Badge>;
    default: return <Badge variant="secondary" className="text-xs">{s}</Badge>;
  }
};

export function RequestorDashboard() {
  const navigate = useNavigate();
  const { jobId, jobToken } = useJob();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [notifs, setNotifs] = useState<Notification[]>([]);
  const [skillName, setSkillName] = useState("—");
  const [skillId, setSkillId] = useState("—");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (!jobId) return;
    api.getQuestions(jobId).then(setQuestions).catch(() => {});
    api.getJob(jobId).then((j) => { setSkillName(j.skill_name); setSkillId(j.skill_id); }).catch(() => {});
    if (jobToken) api.getNotifications(jobToken).then(setNotifs).catch(() => {});
  }, [jobId, jobToken]);

  const markAllRead = async () => {
    if (!jobToken) return;
    await api.markAllNotificationsRead(jobToken);
    setNotifs((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const downloadExcel = async (type: "draft" | "approved") => {
    if (!jobId) return;
    setDownloading(true);
    try {
      const blob = await api.getExport(jobId, type);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `${skillName}-${skillId}-${type}.xlsx`; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { alert(e instanceof Error ? e.message : "Download failed."); }
    finally { setDownloading(false); }
  };

  const accepted = questions.filter((q) => q.status === "accepted").length;
  const rejected = questions.filter((q) => q.status === "rejected").length;
  const pending = questions.filter((q) => q.status === "pending").length;
  const total = questions.length;
  const unreadCount = notifs.filter((n) => !n.read).length;

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <h2 className="text-2xl text-[#1F1F29]">Requestor Dashboard</h2>
        <p className="text-sm text-gray-600">Monitor SME review progress, notifications, and download options.</p>
      </div>

      {!jobId && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          No active job. <button className="underline" onClick={() => navigate("/")}>Start from Input</button>.
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-5 lg:grid-cols-10">
        {[
          { label: "Skill", value: skillName.slice(0, 10) },
          { label: "SSID", value: skillId },
          { label: "Total Q", value: String(total) },
          { label: "Accepted", value: String(accepted), color: "text-green-600" },
          { label: "Rejected", value: String(rejected), color: "text-red-600" },
          { label: "Pending", value: String(pending) },
          { label: "Dup Warnings", value: String(questions.filter((q) => q.duplicate_warning).length), color: "text-amber-600" },
          { label: "Job ID", value: jobId?.slice(0, 6) ?? "—" },
          { label: "Notifications", value: String(notifs.length) },
          { label: "Unread", value: String(unreadCount), color: unreadCount > 0 ? "text-[#A100FF]" : undefined },
        ].map((m) => (
          <Card key={m.label}><CardContent className="pt-4 pb-3">
            <div className="text-center">
              <p className={`text-lg ${m.color ?? "text-[#1F1F29]"}`}>{m.value}</p>
              <p className="text-[10px] text-gray-500 leading-tight">{m.label}</p>
            </div>
          </CardContent></Card>
        ))}
      </div>

      <Card><CardContent className="pt-5">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">SME Review Progress</span>
            <span className="text-[#1F1F29]">Accepted {accepted} / {total}</span>
          </div>
          <Progress value={total > 0 ? (accepted / total) * 100 : 0} className="h-2.5 [&>div]:bg-[#A100FF]" />
          <p className="text-xs text-gray-500">{pending} questions still pending review.</p>
        </div>
      </CardContent></Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <Card className="h-full">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Bell className="h-4 w-4 text-[#A100FF]" />
                  SME Review Notifications
                  {unreadCount > 0 && <Badge className="bg-[#A100FF] text-xs">{unreadCount}</Badge>}
                </CardTitle>
                <Button variant="ghost" size="sm" className="text-xs" onClick={markAllRead}>Mark All Read</Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {notifs.length === 0 && <p className="text-xs text-gray-400">No notifications yet.</p>}
              {notifs.map((n) => (
                <div key={n.id} className={`rounded-lg border p-3 ${!n.read ? "border-[#A100FF]/40 bg-[#A100FF]/5" : "bg-[#F7F7FA]"}`}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className="text-xs text-[#1F1F29]">{n.message}</p>
                      <p className="mt-1 text-[10px] text-gray-400">{new Date(n.created_at).toLocaleTimeString()}</p>
                    </div>
                    {!n.read && <div className="h-2 w-2 rounded-full bg-[#A100FF] mt-1 shrink-0" />}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2">
          <Card>
            <CardHeader><CardTitle className="text-base">Question Status Table</CardTitle></CardHeader>
            <CardContent>
              <div className="overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>title</TableHead><TableHead>topic</TableHead>
                      <TableHead>career_level</TableHead><TableHead>complexity</TableHead>
                      <TableHead>status</TableHead><TableHead>last_action</TableHead>
                      <TableHead>dup</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {questions.slice(0, 20).map((q) => (
                      <TableRow key={q.id}>
                        <TableCell className="text-xs">{q.title}</TableCell>
                        <TableCell className="max-w-[120px]"><p className="text-xs truncate">{q.topic}</p></TableCell>
                        <TableCell><Badge variant="outline" className="text-xs">{q.career_level}</Badge></TableCell>
                        <TableCell className="text-xs">{q.complexity}</TableCell>
                        <TableCell>{statusBadge(q.status)}</TableCell>
                        <TableCell className="text-xs text-gray-600">{q.last_sme_action}</TableCell>
                        <TableCell>
                          {q.duplicate_warning ? <AlertTriangle className="h-4 w-4 text-amber-600" /> : <span className="text-xs text-gray-400">—</span>}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {questions.length === 0 && <p className="py-4 text-center text-xs text-gray-400">No questions yet.</p>}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="border-2">
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Download className="h-5 w-5 text-gray-600" />Download Current Draft Excel</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-xs text-gray-600">Always available once generated rows exist. May include questions not fully accepted by SME.</p>
            <Badge variant="outline" className="border-amber-600 text-amber-600 text-xs"><AlertTriangle className="mr-1 h-3 w-3" />Some questions may still be pending SME review.</Badge>
            <Button variant="outline" className="w-full" onClick={() => downloadExcel("draft")} disabled={downloading}>
              <Download className="mr-2 h-4 w-4" />{downloading ? "Downloading…" : "Download Draft Excel"}
            </Button>
          </CardContent>
        </Card>
        <Card className="border-2 border-green-600">
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Download className="h-5 w-5 text-green-600" />Download Approved Excel</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-xs text-gray-600">Available after all questions are accepted or final override is confirmed.</p>
            <Badge className="bg-green-600 text-xs"><CheckCircle2 className="mr-1 h-3 w-3" />SME Review Complete</Badge>
            <Button onClick={() => downloadExcel("approved")} disabled={downloading} className="w-full bg-green-600 hover:bg-green-700">
              <Download className="mr-2 h-4 w-4" />{downloading ? "Downloading…" : "Download Approved Excel"}
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-between">
        <Button variant="outline" onClick={() => navigate("/progress")}>Back to Generation</Button>
        <Button onClick={() => navigate("/send-review")} className="bg-[#A100FF] hover:bg-[#8A00DD]">Send to SME Review</Button>
      </div>
    </div>
  );
}
