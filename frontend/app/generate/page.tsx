"use client";

import { Copy, Loader2, Sparkles } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DraftBanner } from "@/components/ui/draft-banner";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import Link from "next/link";
import { Columns3 } from "lucide-react";
import { streamSSE } from "@/lib/api-client";

export default function GeneratePage() {
  const [rawInput, setRawInput] = useState("");
  const [toneHint, setToneHint] = useState("");
  const [output, setOutput] = useState("");
  const [hashtags, setHashtags] = useState<string[]>([]);
  const [styleCount, setStyleCount] = useState<number | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    if (!rawInput.trim()) return;
    setStreaming(true);
    setOutput("");
    setHashtags([]);
    setStyleCount(null);
    setError(null);
    setCopied(false);

    await streamSSE(
      "/posts/generate",
      { raw_input: rawInput, tone_hint: toneHint || null },
      {
        onToken: (text) => setOutput((prev) => prev + text),
        onEvent: (event, data) => {
          if (event === "style_examples_used") setStyleCount(data.count);
          if (event === "done") setHashtags(data.hashtags ?? []);
        },
        onError: (msg) => setError(msg),
      }
    );

    setStreaming(false);
  }

  async function copyToClipboard() {
    const text = hashtags.length ? `${output}\n\n${hashtags.map((h) => `#${h}`).join(" ")}` : output;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="px-8 py-8 max-w-3xl">
      <h1 className="font-display text-2xl font-semibold">Generate a post</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Drop in bullet points, a topic, or a draft. We match it to the voice of your own past posts.
      </p>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-muted-foreground">Raw material</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            placeholder="e.g. Shipped a new caching layer this week, cut p95 latency by 40%. Want to share the approach we took..."
            value={rawInput}
            onChange={(e) => setRawInput(e.target.value)}
            className="min-h-32"
          />
          <Input
            placeholder="Optional steering, e.g. 'more casual' or 'announcement style'"
            value={toneHint}
            onChange={(e) => setToneHint(e.target.value)}
          />
          <Button onClick={generate} disabled={streaming || !rawInput.trim()}>
            {streaming ? (
              <>
                <Loader2 size={14} className="animate-spin" /> Generating
              </>
            ) : (
              <>
                <Sparkles size={14} /> Generate post
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {error && <p className="mt-4 text-sm text-destructive">{error}</p>}

      {(output || streaming) && (
        <Card className="mt-4">
          <CardContent className="space-y-3 pt-5">
            <div className="flex items-center justify-between">
              <DraftBanner label="Draft -- review before posting" />
              {styleCount !== null && (
                <span className="text-xs text-muted-foreground">
                  Styled from {styleCount} of your past post{styleCount === 1 ? "" : "s"}
                </span>
              )}
            </div>

            <Textarea value={output} onChange={(e) => setOutput(e.target.value)} className="min-h-48" />

            {hashtags.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {hashtags.map((h) => (
                  <span key={h} className="rounded-full bg-muted px-2.5 py-0.5 text-xs text-muted-foreground">
                    #{h}
                  </span>
                ))}
              </div>
            )}

            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={generate} disabled={streaming}>
                Regenerate
              </Button>
              <Button size="sm" variant="ghost" onClick={copyToClipboard} disabled={!output}>
                <Copy size={14} /> {copied ? "Copied" : "Copy"}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Copy this and post it on LinkedIn yourself -- nothing here publishes automatically.
            </p>
          </CardContent>
        </Card>
      )}

      <Card className="mt-3 border-dashed">
        <CardContent className="flex items-center justify-between py-3">
          <div>
            <p className="text-sm font-medium">Want to see 3 styles at once?</p>
            <p className="text-xs text-muted-foreground">Professional, casual, and storytelling — generated in parallel.</p>
          </div>
          <Link href="/generate/variants">
            <Button size="sm" variant="outline">
              <Columns3 size={14} /> Try variants
            </Button>
          </Link>
        </CardContent>
      </Card>

    </div>
  );
}