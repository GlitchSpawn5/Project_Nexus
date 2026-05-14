"use client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { listUsers, getUsageStats } from "@/lib/api/admin";
import { getLLMStatus } from "@/lib/api/llm";
import { UserTable } from "@/components/admin/UserTable";
import { UsageStatsPanel } from "@/components/admin/UsageStats";
import { LLMStatusCard } from "@/components/admin/LLMStatusCard";
import { Topbar } from "@/components/shell/Topbar";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useAuthStore } from "@/lib/stores/auth";
import { useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { KeyRound, Route, Shield, Users } from "lucide-react";

export function AdminPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const qc = useQueryClient();

  useEffect(() => {
    if (user && user.role !== "admin") {
      navigate("/dashboard");
    }
  }, [user, navigate]);

  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: listUsers,
    enabled: user?.role === "admin",
  });

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["admin-usage"],
    queryFn: getUsageStats,
    enabled: user?.role === "admin",
  });

  const { data: llmStatus, isLoading: llmLoading } = useQuery({
    queryKey: ["llm-status"],
    queryFn: getLLMStatus,
    enabled: user?.role === "admin",
    staleTime: 30_000,
  });

  if (!user || user.role !== "admin") {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Shield className="mx-auto mb-3 h-10 w-10 text-white/20" />
          <p className="text-white/40">Admin access required</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Topbar title="Admin" />
      <div className="page-shell space-y-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-teal-300/75">
            Governance
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-white">Security and operations</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-white/45">
            Manage access, monitor adoption, and verify LLM provider fallback health from one control
            surface.
          </p>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <AdminSignal icon={Users} label="Identity" text="Role-controlled users" />
          <AdminSignal icon={KeyRound} label="Access" text="Space-level governance" />
          <AdminSignal icon={Route} label="Resilience" text="Provider fallback chain" />
        </div>

        <Tabs defaultValue="users">
          <TabsList className="mb-6">
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="usage">Usage</TabsTrigger>
            <TabsTrigger value="llm">LLM Status</TabsTrigger>
          </TabsList>

          <TabsContent value="users">
            {usersLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="section-panel h-12 animate-pulse rounded-lg" />
                ))}
              </div>
            ) : (
              <UserTable
                users={users ?? []}
                onUpdated={() => qc.invalidateQueries({ queryKey: ["admin-users"] })}
              />
            )}
          </TabsContent>

          <TabsContent value="usage">
            {statsLoading ? (
              <div className="grid grid-cols-5 gap-4">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="section-panel h-24 animate-pulse rounded-lg" />
                ))}
              </div>
            ) : stats ? (
              <UsageStatsPanel stats={stats} />
            ) : null}
          </TabsContent>

          <TabsContent value="llm">
            <LLMStatusCard status={llmStatus} isLoading={llmLoading} />
          </TabsContent>
        </Tabs>
      </div>
    </>
  );
}

function AdminSignal({
  icon: Icon,
  label,
  text,
}: {
  icon: React.ElementType;
  label: string;
  text: string;
}) {
  return (
    <div className="section-panel rounded-lg p-4">
      <Icon className="h-4 w-4 text-teal-300" />
      <p className="mt-3 text-sm font-medium text-white/80">{label}</p>
      <p className="mt-1 text-xs text-white/36">{text}</p>
    </div>
  );
}
