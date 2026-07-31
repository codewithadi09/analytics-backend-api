import { useState } from "react";
import { SidebarContent } from "@/components/layout/Sidebar";

export function MobileTopBar() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3 md:hidden">
        <span className="text-sm font-medium text-zinc-900">OneCX Analytics</span>
        <button
          aria-label="Open menu"
          className="btn-secondary !px-2.5 !py-1.5"
          onClick={() => setOpen(true)}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {open && (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            aria-label="Close menu"
            className="fixed inset-0 bg-zinc-900/20"
            onClick={() => setOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 w-64 bg-white px-3 py-6 shadow-lg">
            <SidebarContent onNavigate={() => setOpen(false)} />
          </div>
        </div>
      )}
    </>
  );
}
