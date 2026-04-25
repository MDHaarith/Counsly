import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col px-5 py-8">
      <section className="flex flex-1 flex-col justify-center gap-8">
        <div className="space-y-5">
          <p className="text-sm font-medium text-olive-gray">TNEA counselling guidance</p>
          <h1 className="font-serif text-[42px] font-medium leading-tight text-anthracite">Make your choice list with calmer evidence.</h1>
          <p className="max-w-[32ch] text-base leading-relaxed text-olive-gray">
            Counsly turns marks, rank bands, historical cutoffs, and college data into a practical counselling workspace.
          </p>
        </div>
        <Link href="/login">
          <Button>Start with Google</Button>
        </Link>
        <div className="grid gap-3">
          <Card>
            <h2 className="font-serif text-lg font-medium">Historical rank band</h2>
            <p className="mt-1 text-sm leading-relaxed text-olive-gray">Range-based guidance from past TNEA data. No fake exact predictions.</p>
          </Card>
          <Card>
            <h2 className="font-serif text-lg font-medium">Choice filing</h2>
            <p className="mt-1 text-sm leading-relaxed text-olive-gray">Build, reorder, and export a clean list your family can review.</p>
          </Card>
        </div>
      </section>
    </main>
  );
}
