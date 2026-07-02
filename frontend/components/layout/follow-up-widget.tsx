"use client";

import { CheckCircle2, Clock } from "lucide-react";
import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CategoryBadge } from "@/components/ui/category-badge";
import { useFollowUps, useMarkActioned } from "@/hooks/use-jobs-and-connections";

export function FollowUpWidget() {
  const { data: messages = [], isLoading } = useFollowUps(3);
  const markActioned = useMarkActioned();

  if (isLoading) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Clock size={14} className="text-priority-recruiter" />
          Follow-ups needed
        </CardTitle>
        <Link
          href="/follow-ups"
          className="text-xs text-primary underline-offset-4 hover:underline"
        >
          View all
        </Link>
      </CardHeader>
      <CardContent className="space-y-1.5">
        {messages.length === 0 && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground py-1">
            <CheckCircle2 size={13} className="text-priority-collaboration" />
            All clear — no pending follow-ups
          </div>
        )}
        {messages.slice(0, 4).map((m) => (
          <div
            key={m.id}
            className="flex items-center justify-between gap-2 rounded-md border border-border px-3 py-2"
          >
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <p className="truncate text-xs font-medium">{m.sender_name}</p>
                <CategoryBadge category={m.category} className="text-[10px]" />
              </div>
              <p className="truncate text-xs text-muted-foreground">{m.summary ?? m.content}</p>
            </div>
            <button
              onClick={() => markActioned.mutate(m.id)}
              className="shrink-0 rounded p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              title="Mark as done"
            >
              <CheckCircle2 size={14} />
            </button>
          </div>
        ))}
        {messages.length > 4 && (
          <Link
            href="/follow-ups"
            className="block text-center text-xs text-muted-foreground hover:text-foreground py-1"
          >
            +{messages.length - 4} more
          </Link>
        )}
      </CardContent>
    </Card>
  );
}
