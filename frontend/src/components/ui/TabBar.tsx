"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/dashboard", label: "Home" },
  { href: "/recommendations", label: "Recs" },
  { href: "/choices", label: "Choices" },
  { href: "/explore", label: "Explore" },
  { href: "/profile", label: "Profile" },
];

export function TabBar() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-border-cream bg-ivory/95 px-2 pb-[env(safe-area-inset-bottom)] backdrop-blur">
      <div className="mx-auto grid h-16 max-w-md grid-cols-5 gap-1">
        {tabs.map((tab) => {
          const active = pathname === tab.href || pathname.startsWith(`${tab.href}/`);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={[
                "flex min-h-12 items-center justify-center rounded-xl text-sm font-medium transition-colors",
                active ? "bg-surface-alt text-anthracite" : "text-stone-gray hover:text-anthracite",
              ].join(" ")}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
