"use client";

import { ChevronDown, Loader2, Sparkles } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { ReplyDraftPanel } from "@/components/inbox/reply-draft-panel";
import { Button } from "@/components/ui/button";
import { CategoryBadge, PriorityRail } from "@/components/ui/category-badge";
import { Textarea } from "@/components/ui/textarea";
import { useExtractJob } from "@/hooks/use-jobs-and-connections";
import { useMessages } from "@/hooks/use-messages";
import { useUpdateBioContext, useUserProfile } from "@/hooks/use-user";
import { cn } from "@/lib/utils";

const CATEGORIES = ["all", "recruiter", "collaboration", "genuine", "general", "spam", "needs_review"] as const;

export default function InboxPage() {
  const [category, setCategory] = useState<(typeof CATEGORIES)[number]>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [extractedIds, setExtractedIds] = useState<Set<string>>(new Set());

  const { data: messages, isLoading } = useMessages(category === "all" ? undefined : { category });
  const { data: profile } = useUserProfile();
  const updateBio = useUpdateBioContext();
  const extractJob = useExtractJob();
  const [bioDraft, setBioDraft] = useState("");
  const bioContext = bioDraft || profile?.bio_context || "";

  const sorted = useMemo(
    () => [...(messages ?? [])].sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0)),
    [messages]
  );

  return (
    <div className="px-8 py-8 max-w-4xl">
      <h1 className="font-display text-2xl font-semibold">Inbox</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Sorted by priority. Recruiter and collaboration messages float to the top.
      </p>

      <div className="mt-4 rounded-md border border-border bg-muted/30 p-3">
        <label className="text-xs font-medium text-muted-foreground">
          Your context (used to tailor reply drafts)
        </label>
        <Textarea
          placeholder="e.g. Backend engineer open to senior roles, not interested in sales pitches."
          defaultValue={profile?.bio_context ?? ""}
          onChange={(e) => setBioDraft(e.target.value)}
          onBlur={() => bioDraft && updateBio.mutate(bioDraft)}
          className="mt-1 min-h-16 bg-background"
        />
      </div>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {CATEGORIES.map((c) => (
          <button
            key={c}
            onClick={() => setCategory(c)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium capitalize transition-colors",
              category === c
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border text-muted-foreground hover:bg-muted"
            )}
          >
            {c.replace("_", " ")}
          </button>
        ))}
      </div>

      <div className="mt-5 space-y-2">
        {isLoading && <p className="text-sm text-muted-foreground">Loading messages...</p>}
        {!isLoading && sorted.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No messages here yet. Import your LinkedIn data export to populate your inbox.
          </p>
        )}

        {sorted.map((m) => {
          const expanded = expandedId === m.id;
          const isRecruiter = m.category === "recruiter";
          const alreadyExtracted = extractedIds.has(m.id);

          return (
            <div key={m.id} className="flex gap-3 rounded-md border border-border bg-card">
              <PriorityRail category={m.category} />
              <div className="flex-1 py-3 pr-3">
                <button
                  className="flex w-full items-start justify-between gap-3 text-left"
                  onClick={() => setExpandedId(expanded ? null : m.id)}
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium">{m.sender_name}</p>
                      <CategoryBadge category={m.category} />
                    </div>
                    <p className="mt-0.5 truncate text-sm text-muted-foreground">
                      {m.summary ?? m.content}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    {m.priority_score !== null && (
                      <span className="font-data text-xs text-muted-foreground">
                        {Math.round(m.priority_score)}
                      </span>
                    )}
                    <ChevronDown
                      size={16}
                      className={cn("transition-transform text-muted-foreground", expanded && "rotate-180")}
                    />
                  </div>
                </button>

                {expanded && (
                  <div className="mt-3 space-y-4">
                    <p className="whitespace-pre-wrap rounded-md bg-muted/40 p-3 text-sm">{m.content}</p>

                    {/* Extract opportunity button — only for recruiter messages */}
                    {isRecruiter && (
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={extractJob.isPending || alreadyExtracted}
                          onClick={async () => {
                            try {
                              await extractJob.mutateAsync(m.id);
                              setExtractedIds((prev) => new Set([...prev, m.id]));
                            } catch {
                              /* error surfaced via mutation state below */
                            }
                          }}
                        >
                          {extractJob.isPending && extractJob.variables === m.id ? (
                            <><Loader2 size={13} className="animate-spin" /> Extracting...</>
                          ) : alreadyExtracted ? (
                            "✓ Added to jobs"
                          ) : (
                            <><Sparkles size={13} /> Extract opportunity</>
                          )}
                        </Button>
                        {alreadyExtracted && (
                          <Link href="/jobs" className="text-xs text-primary underline-offset-4 hover:underline">
                            View in Jobs →
                          </Link>
                        )}
                      </div>
                    )}

                    <ReplyDraftPanel message={m} bioContext={bioContext} />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
