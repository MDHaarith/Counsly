"use client";

import { Button } from "@/components/ui/Button";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export function LoginClient() {
  function startGoogle() {
    window.location.href = `${API_URL}/api/auth/google/start`;
  }

  return <Button onClick={startGoogle}>Continue with Google</Button>;
}
