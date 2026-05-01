import { AuthNavWrapper } from "@/components/AuthNavWrapper";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthNavWrapper>
      {children}
    </AuthNavWrapper>
  );
}
