import { Card } from "@/components/ui/Card";
import { LoginClient } from "@/components/auth/LoginClient";

export default function LoginPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-5 py-8">
      <div className="space-y-6">
        <div>
          <p className="text-sm font-medium text-olive-gray">Counsly account</p>
          <h1 className="mt-2 font-serif text-[34px] font-medium leading-tight">Continue with Google</h1>
          <p className="mt-3 text-sm leading-relaxed text-olive-gray">
            Your workspace keeps marks, choices, and payment access together for this counselling season.
          </p>
        </div>
        <Card>
          <LoginClient />
          <p className="mt-4 text-xs leading-relaxed text-stone-gray">
            No password. Counsly stores your Google ID only as an identity reference.
          </p>
        </Card>
      </div>
    </main>
  );
}
