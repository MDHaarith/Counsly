import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export default function NotFoundPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-5">
      <Card variant="featured">
        <p className="text-sm font-medium text-olive-gray">404</p>
        <h1 className="mt-1 font-serif text-3xl font-medium leading-tight">This page is not available</h1>
        <p className="mt-3 text-sm leading-relaxed text-olive-gray">
          The route may have moved, or the counselling step is not open yet.
        </p>
        <Link href="/dashboard">
          <Button className="mt-5">Go to dashboard</Button>
        </Link>
      </Card>
    </main>
  );
}
