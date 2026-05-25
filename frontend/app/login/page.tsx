import Link from "next/link";

import { LoginCard } from "@/components/login-card";
import { Badge } from "@/components/ui";

export default function LoginPage() {
  return (
    <div className="grid min-h-[calc(100vh-6rem)] items-center gap-8 lg:grid-cols-[minmax(0,1fr)_440px]">
      <div className="space-y-5">
        <Link className="brand" href="/">
          <span className="brand-mark" />
          <span>Counsly</span>
        </Link>
        <Badge>Login</Badge>
        <h1 className="display-title max-w-3xl">Return to the shortlist you already started.</h1>
        <p className="copy max-w-xl">
          Your workspace carries onboarding progress, compares, snapshots, and filing notes.
        </p>
      </div>
      <LoginCard compact />
    </div>
  );
}
