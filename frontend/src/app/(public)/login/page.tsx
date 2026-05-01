"use client";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export default function LoginPage() {
  function startGoogle() {
    window.location.href = `${API_URL}/api/auth/google/start`;
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-5 py-8">
      <div className="space-y-6">
        <div>
          <p className="text-sm font-medium text-olive-gray">Counsly account</p>
          <h1 className="mt-2 font-serif text-[34px] font-medium leading-tight">Continue with Google</h1>
          <p className="mt-3 text-sm leading-relaxed text-olive-gray">Your workspace keeps marks, choices, and payment access together for this counselling season.</p>
        </div>
        <Card>
          <Button onClick={startGoogle}>Continue with Google</Button>
          <p className="mt-4 text-xs leading-relaxed text-stone-gray">No password. Counsly stores your Google ID only as an identity reference.</p>
        </Card>
      </div>
    </main>
  );
}
