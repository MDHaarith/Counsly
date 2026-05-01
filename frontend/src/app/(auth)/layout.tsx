import { AuthNavWrapper } from "@/components/AuthNavWrapper";

export const dynamic = "force-dynamic";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthNavWrapper>
      {children}
    </AuthNavWrapper>
  );
}
