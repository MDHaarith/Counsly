import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export default function MaintenancePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-5">
      <Card variant="featured">
        <p className="text-sm font-medium text-olive-gray">Maintenance</p>
        <h1 className="mt-1 font-serif text-[30px] font-medium leading-tight">Counsly is being updated</h1>
        <p className="mt-3 text-sm leading-relaxed text-olive-gray">
          We are applying a data or product update. Existing choices and profile details stay safe.
        </p>
        <Link href="/">
          <Button className="mt-5">Check again</Button>
        </Link>
      </Card>
    </main>
  );
}
