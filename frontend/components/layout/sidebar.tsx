"use client";

import {
  BarChart3,
  Briefcase,
  Clock,
  Columns3,
  Inbox,
  LayoutDashboard,
  PenSquare,
  ScrollText,
  Upload,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard",   label: "Dashboard",  icon: LayoutDashboard },
  { href: "/inbox",       label: "Inbox",      icon: Inbox },
  { href: "/follow-ups",  label: "Follow-ups", icon: Clock },
  { href: "/generate",    label: "Generate",   icon: PenSquare },
  { href: "/generate/variants", label: "Variants", icon: Columns3, sub: true },
  { href: "/jobs",        label: "Jobs",       icon: Briefcase },
  { href: "/connections", label: "Network",    icon: Users },
  { href: "/analytics",   label: "Analytics",  icon: BarChart3 },
  { href: "/reports",     label: "Reports",    icon: ScrollText },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex md:flex-col md:w-60 md:shrink-0 border-r border-border bg-card">
      <div className="px-6 py-6">
        <Link href="/dashboard" className="font-display text-xl font-semibold tracking-tight">
          LinkedIQ
        </Link>
        <p className="mt-1 text-xs text-muted-foreground">
          Built on your export. Nothing auto-sends.
        </p>
      </div>

      <nav className="flex-1 px-3 space-y-0.5">
        {NAV_ITEMS.map(({ href, label, icon: Icon, sub }) => {
          const active =
            href === "/generate"
              ? pathname === "/generate"
              : pathname?.startsWith(href);

          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "group relative flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                sub && "pl-8 text-xs",
                active
                  ? "bg-muted text-foreground font-medium"
                  : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
              )}
            >
              <span
                className={cn(
                  "absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-full transition-opacity",
                  active ? "bg-primary opacity-100" : "opacity-0"
                )}
              />
              <Icon size={sub ? 14 : 16} strokeWidth={2} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 pb-4 pt-2">
        <Link
          href="/import"
          className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted/60 hover:text-foreground transition-colors"
        >
          <Upload size={16} strokeWidth={2} />
          Import data
        </Link>
      </div>
    </aside>
  );
}
