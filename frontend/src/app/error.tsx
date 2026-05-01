"use client";

import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-5">
      <Card variant="featured">
        <p className="text-sm font-medium text-olive-gray">Something went wrong</p>
        <h1 className="mt-1 font-serif text-3xl font-medium leading-tight">Counsly could not load this screen</h1>
        <p className="mt-3 text-sm leading-relaxed text-olive-gray">
          {error.message || "Try again. If this repeats, return to the dashboard and continue from there."}
        </p>
        <div className="mt-5 grid gap-2">
          <Button onClick={reset}>Try again</Button>
          <Link href="/dashboard">
            <Button variant="secondary">Go to dashboard</Button>
          </Link>
        </div>
      </Card>
    </main>
  );
}
