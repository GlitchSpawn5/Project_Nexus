"use client";
import { Bell, CircleCheck, ServerCog } from "lucide-react";
import { useAuthStore } from "@/lib/stores/auth";

export function Topbar({ title }: { title?: string }) {
  const { user } = useAuthStore();

  return (
    <header className="flex h-16 items-center justify-between border-b border-white/10 bg-[#080b10]/70 px-6 backdrop-blur">
      <div>
        <h2 className="text-sm font-semibold text-white/82">{title}</h2>
        <p className="mt-0.5 text-xs text-white/32">Enterprise knowledge intelligence platform</p>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 rounded-lg border border-teal-300/18 bg-teal-300/8 px-3 py-1.5 text-xs text-teal-100/75 sm:flex">
          <CircleCheck className="h-3.5 w-3.5 text-teal-300" />
          Platform online
        </div>
        <div className="hidden items-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-white/48 md:flex">
          <ServerCog className="h-3.5 w-3.5" />
          {user?.role ?? "viewer"}
        </div>
        <button className="rounded-lg p-1.5 text-white/32 transition-all hover:bg-white/5 hover:text-white/75">
          <Bell className="h-4 w-4" />
        </button>
        <div className="h-7 w-px bg-white/10" />
        <span className="text-xs text-white/40">{user?.email}</span>
      </div>
    </header>
  );
}
