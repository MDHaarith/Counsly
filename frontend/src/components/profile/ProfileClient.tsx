"use client";

import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { apiClient } from "@/lib/api";

export function ProfileClient({ isPaid }: { isPaid: boolean }) {
  async function logout() {
    try {
      await apiClient("/api/auth/logout", { method: "POST" });
    } catch (err) {
      console.error("Logout failed", err);
    }
    window.location.href = "/login";
  }

  return (
    <div className="space-y-4">
      <Button variant="secondary" onClick={logout}>
        Log out
      </Button>
      {!isPaid && (
        <Link href="/subscribe?from=profile">
          <Button>Unlock Full Access</Button>
        </Link>
      )}
    </div>
  );
}
