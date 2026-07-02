"use client";

import { Copy, Loader2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { DraftBanner } from "@/components/ui/draft-banner";
import { Textarea } from "@/components/ui/textarea";
import { streamSSE } from "@/lib/api-client";
import type { Message } from "@/lib/types";

export function ReplyDraftPanel({ message, bioContext }: { message: Message; bioContext: string }) {
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    setStreaming(true);
    setDraft("");
    setError(null);
    setCopied(false);

    await streamSSE(
      `/messages/${message.id}/draft-reply`,
      { bio_context: bioContext },
      {
        onToken: (text) => setDraft((prev) => prev + text),
        onError: (msg) => setError(msg),
      }
    );

    setStreaming(false);
  }

  async function copyToClipboard() {
    await navigator.clipboard.writeText(draft);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="space-y-3 border-t border-border pt-4">
      <div className="flex items-center justify-between">
        <DraftBanner />
        <Button size="sm" variant="outline" onClick={generate} disabled={streaming}>
          {streaming ? (
            <>
              <Loader2 size={14} className="animate-spin" /> Generating
            </>
          ) : draft ? (
            "Regenerate"
          ) : (
            "Draft reply"
          )}
        </Button>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {(draft || streaming) && (
        <>
          <Textarea value={draft} onChange={(e) => setDraft(e.target.value)} className="min-h-32" />
          <Button size="sm" variant="ghost" onClick={copyToClipboard} disabled={!draft}>
            <Copy size={14} /> {copied ? "Copied" : "Copy to clipboard"}
          </Button>
          <p className="text-xs text-muted-foreground">
            This is a draft. Copy it and send it from LinkedIn yourself -- nothing here sends messages for you.
          </p>
        </>
      )}
    </div>
  );
}
