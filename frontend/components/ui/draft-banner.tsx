import { PenLine } from "lucide-react";

import { cn } from "@/lib/utils";

export function DraftBanner({
  label = "Draft -- review before sending",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-md border border-accent/30 bg-accent/10 px-3 py-1.5 text-xs font-medium text-accent",
        className
      )}
    >
      <PenLine size={13} strokeWidth={2.25} />
      {label}
    </div>
  );
}
