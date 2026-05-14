"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster
        theme="dark"
        style={{
          background: "rgba(15,15,25,0.95)",
          border: "1px solid rgba(255,255,255,0.1)",
          color: "#e8e8f0",
        }}
      />
    </QueryClientProvider>
  );
}
