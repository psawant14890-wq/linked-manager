"use client";

import { CheckCircle2, Clock } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { CategoryBadge, PriorityRail } from "@/components/ui/category-badge";
import { type FollowUpMessage, useFollowUps, useMarkActioned } from "@/hooks/use-jobs-and-connections";
import { cn } from "@/lib/utils";

function FollowUpRow({ message }: { message: FollowUpMessage }) {
  const markActioned = useMarkActioned();
  const [expanded, setExpanded] = useState(false);
  const [done, setDone] = useState(false);

  async function handleMark() {
    setDone(true);
    await markActioned.mutateAsync(message.id);
  }

  if (done) return null;

  return (
    <div className="flex gap-3 rounded-md border border-border bg-card opacity-100 transition-opacity">
      <PriorityRail category={message.category} />
      <div className="flex-1 py-3 pr-3">
        <div className="flex items-start justify-between gap-3">
          <button className="min-w-0 text-left flex-1" onClick={() => setExpanded((e) => !e)}>
            <div className="flex items-center gap-2">
              <p className="text-sm font-medium">{message.sender_name}</p>
              <CategoryBadge category={message.category} />
            </div>
            <p className="mt-0.5 truncate text-sm text-muted-foreground">
              {message.summary ?? message.content}
            </p>
          </button>
          <Button
            size="sm"
            variant="ghost"
            className="shrink-0 text-xs text-muted-foreground hover:text-foreground"
            onClick={handleMark}
            disabled={markActioned.isPending}
          >
            <CheckCircle2 size={14} />
            Done
          </Button>
        </div>

        {expanded && (
          <p className="mt-3 whitespace-pre-wrap rounded-md bg-muted/40 p-3 text-sm">
            {message.content}
          </p>
        )}
      </div>
    </div>
  );
}

export default function FollowUpsPage() {
  const [days, setDays] = useState(3);
  const { data: messages = [], isLoading } = useFollowUps(days);

  return (
    <div className="px-8 py-8 max-w-3xl">
      <div className="flex items-center gap-3">
        <Clock size={20} className="text-priority-recruiter" />
        <h1 className="font-display text-2xl font-semibold">Follow-ups needed</h1>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        Messages where you generated a reply draft but haven&apos;t marked them as done yet. Click{" "}
        <strong>Done</strong> once you&apos;ve sent the reply on LinkedIn manually.
      </p>

      <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
        <span>Older than</span>
        {[1, 3, 7].map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={cn(
              "rounded-full border px-3 py-0.5 text-xs transition-colors",
              days === d
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border hover:bg-muted"
            )}
          >
            {d}d
          </button>
        ))}
      </div>

      <div className="mt-5 space-y-2">
        {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}

        {!isLoading && messages.length === 0 && (
          <div className="rounded-md border border-dashed border-border p-8 text-center">
            <CheckCircle2 size={24} className="mx-auto mb-2 text-priority-collaboration" />
            <p className="text-sm font-medium">All clear</p>
            <p className="mt-1 text-xs text-muted-foreground">
              No outstanding follow-ups right now. Generate a reply draft from the Inbox to start
              tracking.
            </p>
          </div>
        )}

        {messages.map((m) => (
          <FollowUpRow key={m.id} message={m} />
        ))}
      </div>
    </div>
  );
}
