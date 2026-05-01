import { SubscribeClient } from "@/components/subscribe/SubscribeClient";

export default function SubscribePage() {
  return (
    <main className="mx-auto min-h-screen max-w-md px-5 py-8">
      <div className="space-y-5">
        <div>
          <p className="text-sm font-medium text-olive-gray">Full Access</p>
          <h1 className="mt-1 font-serif text-[34px] font-medium leading-tight">Unlock Counsly for ₹149</h1>
          <p className="mt-3 text-sm leading-relaxed text-olive-gray">
            One-time access for this counselling season. No subscription and no auto-renewal.
          </p>
        </div>

        <SubscribeClient />
      </div>
    </main>
  );
}
