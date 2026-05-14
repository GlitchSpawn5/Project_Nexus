"use client";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/lib/stores/auth";
import { useAuth } from "@/lib/hooks/useAuth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const { token, hydrate } = useAuthStore();
  const { isLoading } = useAuth();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    hydrate();
    const stored = localStorage.getItem("nexus_token");
    if (!stored) {
      navigate("/login", { replace: true });
      return;
    }
    const timer = window.setTimeout(() => setChecked(true), 0);
    return () => window.clearTimeout(timer);
  }, [navigate, hydrate]);

  if (!checked || (isLoading && !token)) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0a0a0f]">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
}
