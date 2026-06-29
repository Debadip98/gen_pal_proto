import { useNavigate } from "react-router";
import { Settings, User } from "lucide-react";
import { Badge } from "./ui/badge";
import { useUserType } from "../context/UserTypeContext";

export function AppHeader() {
  const { userType, setUserType } = useUserType();
  const navigate = useNavigate();

  function switchTo(type: "requestor" | "sme") {
    setUserType(type);
    navigate(type === "sme" ? "/sme-review" : "/");
  }

  return (
    <header className="border-b bg-white px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-[#A100FF]">
            <span className="text-xs text-white font-mono">GQ</span>
          </div>
          <h1 className="text-xl text-[#1F1F29]">GenPal Question Bank Factory</h1>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="border-[#A100FF] text-[#A100FF]">
            Mock Mode
          </Badge>
          <div className="flex rounded-lg border border-[#D9D9E3] overflow-hidden">
            <button
              onClick={() => switchTo("requestor")}
              className={`px-3 py-1.5 text-xs transition-colors ${
                userType === "requestor"
                  ? "bg-[#1F1F29] text-white"
                  : "bg-white text-gray-500 hover:bg-[#F7F7FA]"
              }`}
            >
              Requestor
            </button>
            <button
              onClick={() => switchTo("sme")}
              className={`px-3 py-1.5 text-xs transition-colors ${
                userType === "sme"
                  ? "bg-[#A100FF] text-white"
                  : "bg-white text-gray-500 hover:bg-[#F7F7FA]"
              }`}
            >
              SME
            </button>
          </div>
          <button className="rounded-full p-2 hover:bg-[#F7F7FA]">
            <Settings className="h-5 w-5 text-[#1F1F29]" />
          </button>
          <button className="rounded-full p-2 hover:bg-[#F7F7FA]">
            <User className="h-5 w-5 text-[#1F1F29]" />
          </button>
        </div>
      </div>
    </header>
  );
}
