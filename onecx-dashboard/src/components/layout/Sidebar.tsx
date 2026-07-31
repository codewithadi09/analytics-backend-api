import { NavLink } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Traffic & Overview", end: true },
  { to: "/interactions", label: "Interactions & Navigation", end: false },
  { to: "/journey", label: "User Journey", end: false },
  { to: "/engagement", label: "Engagement & Conversion", end: false },
  { to: "/dropoff", label: "Drop-off Group", end: false },
];

function NavItem({ to, label, end }: { to: string; label: string; end: boolean }) {
  return (
    <NavLink to={to} end={end} className={({ isActive }) => (isActive ? "nav-link-active" : "nav-link")}>
      {label}
    </NavLink>
  );
}

export function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { user } = useAuth();

  return (
    <div className="flex h-full flex-col justify-between" onClick={onNavigate}>
      <div>
        <div className="mb-6 px-3 pt-1">
          <span className="text-sm font-medium text-zinc-900">OneCX Analytics</span>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavItem key={item.to} {...item} />
          ))}
          {user?.is_superadmin && (
            <>
              <div className="my-2 border-t border-zinc-100" />
              <NavItem to="/admin" label="Admin Panel" end={false} />
            </>
          )}
        </nav>
      </div>

      <div className="border-t border-zinc-100 pt-3">
        <NavItem to="/account" label="Account" end={false} />
      </div>
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 hidden w-56 border-r border-zinc-200 px-3 py-6 md:block">
      <SidebarContent />
    </aside>
  );
}
