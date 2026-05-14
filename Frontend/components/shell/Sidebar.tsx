"use client";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Search, GitBranch, FileText, Shield, LogOut, Home, Layers3, LockKeyhole,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/stores/auth";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  adminOnly?: boolean;
}

const NAV: NavItem[] = [
  { label: "Knowledge Spaces", href: "/dashboard", icon: Home },
  { label: "Admin", href: "/admin", icon: Shield, adminOnly: true },
];

export function Sidebar({ kbId }: { kbId?: string }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const kbNav: NavItem[] = kbId
    ? [
        { label: "Documents", href: `/kb/${kbId}`, icon: FileText },
        { label: "Query", href: `/kb/${kbId}/query`, icon: Search },
        { label: "Graph", href: `/kb/${kbId}/graph`, icon: GitBranch },
      ]
    : [];

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <aside className="flex h-full w-64 flex-col border-r border-white/10 bg-[#080b10]/88">
      <div className="border-b border-white/10 px-5 py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-300/10 text-teal-300 ring-1 ring-teal-300/25">
            <Layers3 className="h-5 w-5" />
          </div>
          <div>
            <span className="text-lg font-semibold tracking-tight text-white">NEXUS</span>
            <p className="text-[10px] uppercase tracking-[0.24em] text-white/32">Intelligence Platform</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {NAV.filter((n) => !n.adminOnly || user?.role === "admin").map((item) => (
          <SidebarItem key={item.href} item={item} active={pathname === item.href} />
        ))}

        {kbNav.length > 0 && (
          <>
            <div className="mx-2 my-4 border-t border-white/8" />
            <p className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-white/28">
              Active Space
            </p>
            {kbNav.map((item) => (
              <SidebarItem key={item.href} item={item} active={pathname === item.href} />
            ))}
          </>
        )}
      </nav>

      <div className="border-t border-white/10 p-3">
        <div className="mb-3 rounded-lg border border-emerald-300/15 bg-emerald-300/8 px-3 py-2 text-xs text-emerald-100/70">
          <div className="flex items-center gap-2">
            <LockKeyhole className="h-3.5 w-3.5 text-emerald-300" />
            Governed access
          </div>
        </div>
        <div className="flex items-center gap-2 rounded-lg px-2 py-1.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-400/12 text-blue-200 text-xs font-semibold ring-1 ring-blue-300/20">
            {user?.full_name?.[0]?.toUpperCase() ?? "?"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-white/80 truncate">{user?.full_name}</p>
            <p className="text-[10px] text-white/35 truncate">{user?.role}</p>
          </div>
          <button
            onClick={handleLogout}
            className="rounded-md p-1.5 text-white/32 transition-colors hover:bg-white/6 hover:text-white/80"
            title="Sign out"
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}

function SidebarItem({ item, active }: { item: NavItem; active: boolean }) {
  return (
    <Link
      to={item.href}
      className={cn(
        "flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm transition-all",
        active
          ? "bg-white/9 text-white shadow-sm ring-1 ring-white/10"
          : "text-white/50 hover:bg-white/5 hover:text-white/82"
      )}
    >
      <item.icon className="h-4 w-4 shrink-0" />
      {item.label}
    </Link>
  );
}
