import * as React from "react";

import { cn } from "@/lib/utils";

const CATEGORY_LABEL: Record<string, string> = {
  recruiter: "Recruiter",
  collaboration: "Collaboration",
  genuine: "Genuine",
  general: "General",
  spam: "Spam",
  needs_review: "Needs review",
};

const CATEGORY_COLOR_VAR: Record<string, string> = {
  recruiter: "--priority-recruiter",
  collaboration: "--priority-collaboration",
  genuine: "--priority-genuine",
  general: "--priority-general",
  spam: "--priority-spam",
  needs_review: "--priority-general",
};

export function CategoryBadge({ category, className }: { category: string | null; className?: string }) {
  const key = category ?? "needs_review";
  const colorVar = CATEGORY_COLOR_VAR[key] ?? "--priority-general";
  const label = CATEGORY_LABEL[key] ?? key;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        className
      )}
      style={{
        borderColor: `hsl(var(${colorVar}) / 0.35)`,
        color: `hsl(var(${colorVar}))`,
        backgroundColor: `hsl(var(${colorVar}) / 0.08)`,
      }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: `hsl(var(${colorVar}))` }} />
      {label}
    </span>
  );
}

/** The thin vertical "priority rail" used next to inbox rows. */
export function PriorityRail({ category }: { category: string | null }) {
  const key = category ?? "needs_review";
  const colorVar = CATEGORY_COLOR_VAR[key] ?? "--priority-general";
  return <span className="block w-1 self-stretch rounded-full" style={{ backgroundColor: `hsl(var(${colorVar}))` }} />;
}
