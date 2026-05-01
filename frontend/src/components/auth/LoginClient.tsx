"use client";

import { Button } from "@/components/ui/Button";

export function LoginClient() {
  function startGoogle() {
    window.location.href = "/api/auth/google/start";
  }

  return <Button onClick={startGoogle}>Continue with Google</Button>;
}
