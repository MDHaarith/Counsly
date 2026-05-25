import type { ReactNode } from "react";

import { LockKeyhole } from "lucide-react";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  actions?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div className="space-y-3">
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1 className="display-title">{title}</h1>
        <p className="copy max-w-2xl">{description}</p>
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </header>
  );
}

export function Surface({
  children,
  className = "",
  tone = "paper",
}: {
  children: ReactNode;
  className?: string;
  tone?: "paper" | "soft" | "dark" | "coral";
}) {
  return <section className={`surface surface-${tone} ${className}`}>{children}</section>;
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "coral" | "safe" | "warning" | "dark";
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function Metric({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note?: string;
}) {
  return (
    <Surface className="space-y-2 p-4" tone="paper">
      <p className="eyebrow">{label}</p>
      <p className="font-mono text-2xl font-semibold text-counsly-ink">{value}</p>
      {note && <p className="text-sm text-counsly-muted">{note}</p>}
    </Surface>
  );
}

export function PremiumBoard({
  title,
  body,
}: {
  title: string;
  body: string;
}) {
  return (
    <Surface className="relative overflow-hidden p-5" tone="soft">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-counsly-coral/10 text-counsly-coral">
          <LockKeyhole className="h-4 w-4" />
        </span>
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-counsly-ink">{title}</h3>
          <p className="text-sm leading-6 text-counsly-muted">{body}</p>
        </div>
      </div>
    </Surface>
  );
}
