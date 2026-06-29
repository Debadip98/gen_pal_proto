import { Outlet } from "react-router";
import { AppHeader } from "./AppHeader";
import { AppSidebar } from "./AppSidebar";

export function RootLayout() {
  return (
    <div className="flex h-screen flex-col bg-[#F7F7FA]">
      <AppHeader />
      <div className="flex flex-1 overflow-hidden">
        <AppSidebar />
        <main className="flex flex-col flex-1 overflow-auto">
          <div className="flex-1">
            <Outlet />
          </div>
          <footer className="border-t bg-white px-6 py-3">
            <p className="text-xs text-gray-400 text-center">
              Prototype design. Official brand assets and templates should be applied only from approved internal sources.
            </p>
          </footer>
        </main>
      </div>
    </div>
  );
}
