import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { Sidebar } from "@/components/shell/Sidebar";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { DashboardPage } from "./pages/DashboardPage";
import { AdminPage } from "./pages/AdminPage";
import { KBLayout } from "./pages/KBLayout";
import { DocumentsPage } from "./pages/DocumentsPage";
import { QueryPage } from "./pages/QueryPage";
import { GraphPage } from "./pages/GraphPage";

function RootRedirect() {
  const token = localStorage.getItem("nexus_token");
  return <Navigate to={token ? "/dashboard" : "/login"} replace />;
}

function AppLayout() {
  return (
    <AuthGuard>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden bg-transparent">
          <main className="flex-1 overflow-y-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/kb/:kbId" element={<KBLayout />}>
          <Route index element={<DocumentsPage />} />
          <Route path="query" element={<QueryPage />} />
          <Route path="graph" element={<GraphPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
