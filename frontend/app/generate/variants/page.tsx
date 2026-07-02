"use client";

import { Copy, Loader2, Sparkles } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DraftBanner } from "@/components/ui/draft-banner";
import { Textarea } from "@/components/ui/textarea";
import { streamSSE } from "@/lib/api-client";

type Variant = { name: string; text: string; done: boolean };

const STYLE_META: Record<string, { label: string; description: string }> = {
  professional: { label: "Professional", description: "Confident, polished, structured" },
  casual:       { label: "Casual",       description: "Conversational, a little personality" },
  storytelling: { label: "Storytelling", description: "Opens with a scene, builds to the point" },
};

const INITIAL_VARIANTS: Variant[] = [
  { name: "professional", text: "", done: false },
  { name: "casual",       text: "", done: false },
  { name: "storytelling", text: "", done: false },
];

export default function VariantsPage() {
  const [rawInput, setRawInput] = useState("");
  const [variants, setVariants] = useState<Variant[]>(INITIAL_VARIANTS);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const hasAnyOutput = variants.some((v) => v.text.length > 0);

  async function generate() {
    if (!rawInput.trim()) return;
    setGenerating(true);
    setError(null);
    setVariants(INITIAL_VARIANTS.map((v) => ({ ...v, text: "", done: false })));

    await streamSSE(
      "/posts/variants",
      { raw_input: rawInput },
      {
        onEvent: (event, data) => {
          if (event === "variant_done") {
            setVariants((prev) =>
              prev.map((v) =>
                v.name === data.name ? { ...v, text: data.text, done: true } : v
              )
            );
          }
        },
        onError: (msg) => setError(msg),
      }
    );

    setGenerating(false);
  }

  async function copy(text: string, idx: number) {
    await navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 1500);
  }

  return (
    <div className="px-8 py-8 max-w-6xl">
      <h1 className="font-display text-2xl font-semibold">Post variants</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Three styles generated concurrently from the same input — styled to your voice, ready to pick your favourite.
      </p>

      <Card className="mt-6">
        <CardContent className="space-y-3 pt-5">
          <Textarea
            placeholder="Paste bullet points, a project update, or a topic..."
            value={rawInput}
            onChange={(e) => setRawInput(e.target.value)}
            className="min-h-28"
          />
          <Button onClick={generate} disabled={generating || !rawInput.trim()}>
            {generating ? (
              <><Loader2 size={14} className="animate-spin" /> Generating all 3...</>
            ) : (
              <><Sparkles size={14} /> Generate variants</>
            )}
          </Button>
          {generating && (
            <p className="text-xs text-muted-foreground">
              All 3 variants generate in parallel — total time is similar to one single post.
            </p>
          )}
        </CardContent>
      </Card>

      {error && <p className="mt-4 text-sm text-destructive">{error}</p>}

      {hasAnyOutput && (
        <>
          <DraftBanner label="Drafts — review before posting" className="mt-6" />
          <div className="mt-3 grid grid-cols-1 gap-4 lg:grid-cols-3">
            {variants.map((v, i) => {
              const meta = STYLE_META[v.name] ?? { label: v.name, description: "" };
              return (
                <Card key={v.name} className="flex flex-col">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">{meta.label}</CardTitle>
                    <p className="text-xs text-muted-foreground">{meta.description}</p>
                  </CardHeader>
                  <CardContent className="flex flex-1 flex-col gap-3">
                    {!v.done && generating && (
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Loader2 size={12} className="animate-spin" /> Generating...
                      </div>
                    )}
                    {v.text && (
                      <>
                        <Textarea
                          value={v.text}
                          onChange={(e) =>
                            setVariants((prev) =>
                              prev.map((pv, pi) => (pi === i ? { ...pv, text: e.target.value } : pv))
                            )
                          }
                          className="flex-1 min-h-48 text-sm"
                        />
                        <Button size="sm" variant="ghost" onClick={() => copy(v.text, i)}>
                          <Copy size={13} />
                          {copiedIdx === i ? "Copied" : "Copy"}
                        </Button>
                      </>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
