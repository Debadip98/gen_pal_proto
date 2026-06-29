import { Link, useLocation } from "react-router";
import {
  FileInput,
  Search,
  Loader2,
  LayoutDashboard,
  Send,
  ClipboardList,
  MessageSquare,
  RefreshCw,
  Download,
  DollarSign,
  GitBranch,
} from "lucide-react";
import { cn } from "./ui/utils";
import { useUserType } from "../context/UserTypeContext";

const navGroups = [
  {
    label: "Requestor",
    userTypes: ["requestor"] as const,
    items: [
      { path: "/", label: "Input", icon: FileInput },
      { path: "/docs", label: "Docs Discovery", icon: Search },
      { path: "/progress", label: "Generation", icon: Loader2 },
      { path: "/dashboard", label: "Requestor Dashboard", icon: LayoutDashboard },
      { path: "/send-review", label: "Send to SME", icon: Send },
    ],
  },
  {
    label: "SME",
    userTypes: ["sme"] as const,
    items: [
      { path: "/sme-review", label: "SME Review", icon: ClipboardList },
      { path: "/sme-question", label: "Question Review", icon: MessageSquare },
      { path: "/regenerate", label: "Rework", icon: RefreshCw },
      { path: "/version-compare", label: "Version Compare", icon: GitBranch },
      { path: "/doc-check", label: "Doc Alignment", icon: Search },
      { path: "/review-complete", label: "Review Complete", icon: ClipboardList },
    ],
  },
  {
    label: "Output",
    userTypes: ["requestor"] as const,
    items: [
      { path: "/export", label: "Export", icon: Download },
      { path: "/cost", label: "Cost Summary", icon: DollarSign },
      { path: "/flow", label: "Business Flow", icon: GitBranch },
    ],
  },
];

export function AppSidebar() {
  const location = useLocation();
  const { userType } = useUserType();

  const visibleGroups = navGroups.filter((g) =>
    (g.userTypes as readonly string[]).includes(userType)
  );

  const accentColor = userType === "sme" ? "#A100FF" : "#1F1F29";

  return (
    <aside className="w-56 border-r bg-white overflow-y-auto">
      <div
        className="px-4 py-3 border-b"
        style={{ borderLeftColor: accentColor, borderLeftWidth: 3 }}
      >
        <p className="text-[10px] uppercase tracking-widest" style={{ color: accentColor }}>
          {userType === "sme" ? "SME Interface" : "Requestor Interface"}
        </p>
      </div>
      <nav className="flex flex-col gap-4 p-4">
        {visibleGroups.map((group) => (
          <div key={group.label}>
            <p className="mb-1 px-3 text-[10px] uppercase tracking-widest text-gray-400">
              {group.label}
            </p>
            <div className="flex flex-col gap-0.5">
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                      isActive
                        ? "text-white"
                        : "text-[#1F1F29] hover:bg-[#F7F7FA]"
                    )}
                    style={isActive ? { backgroundColor: accentColor } : undefined}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="truncate">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
