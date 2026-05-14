"use client";
import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { setUserRole, deactivateUser } from "@/lib/api/admin";
import type { AdminUser, UserRole } from "@/lib/types/api";
import { UserX } from "lucide-react";
import { formatDate } from "@/lib/utils/format";

const ROLES: UserRole[] = ["admin", "owner", "editor", "viewer"];

export function UserTable({ users, onUpdated }: { users: AdminUser[]; onUpdated: () => void }) {
  const [loading, setLoading] = useState<string | null>(null);

  const handleRole = async (userId: string, role: UserRole) => {
    setLoading(userId);
    try {
      await setUserRole(userId, role);
      toast.success("Role updated");
      onUpdated();
    } catch {
      toast.error("Failed to update role");
    } finally {
      setLoading(null);
    }
  };

  const handleDeactivate = async (userId: string) => {
    setLoading(userId);
    try {
      await deactivateUser(userId);
      toast.success("User deactivated");
      onUpdated();
    } catch {
      toast.error("Failed to deactivate user");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="section-panel overflow-x-auto rounded-lg p-4">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/6 text-left text-xs text-white/35 font-medium">
            <th className="pb-2 pr-4">User</th>
            <th className="pb-2 pr-4">Role</th>
            <th className="pb-2 pr-4">Status</th>
            <th className="pb-2 pr-4">Joined</th>
            <th className="pb-2 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/4">
          {users.map((user) => (
            <tr key={user.id} className="group">
              <td className="py-3 pr-4">
                <div>
                  <p className="text-white/80 font-medium">{user.full_name}</p>
                  <p className="text-xs text-white/35">{user.email}</p>
                </div>
              </td>
              <td className="py-3 pr-4">
                <Select
                  value={user.role}
                  onValueChange={(v) => handleRole(user.id, v as UserRole)}
                  disabled={loading === user.id}
                >
                  <SelectTrigger className="h-7 w-28 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLES.map((r) => (
                      <SelectItem key={r} value={r}>{r}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </td>
              <td className="py-3 pr-4">
                <Badge variant={user.is_active ? "success" : "error"}>
                  {user.is_active ? "Active" : "Inactive"}
                </Badge>
              </td>
              <td className="py-3 pr-4 text-xs text-white/35">{formatDate(user.created_at)}</td>
              <td className="py-3 text-right">
                {user.is_active && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDeactivate(user.id)}
                    disabled={loading === user.id}
                    className="opacity-0 group-hover:opacity-100 transition-opacity gap-1"
                  >
                    <UserX className="h-3.5 w-3.5" />
                    Deactivate
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
