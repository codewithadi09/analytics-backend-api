import { Outlet } from "react-router-dom";
import { Sidebar } from "@/components/layout/Sidebar";
import { MobileTopBar } from "@/components/layout/MobileNav";

export function DashboardShell() {
  return (
    <div className="min-h-screen bg-white">
      <Sidebar />
      <MobileTopBar />
      <main className="md:pl-56">
        <Outlet />
      </main>
    </div>
  );
}
