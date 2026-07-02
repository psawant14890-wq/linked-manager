"use client";

import { format } from "date-fns";
import { Loader2, ScrollText, Sparkles } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useReports } from "@/hooks/use-reports";
import { streamSSE } from "@/lib/api-client";

export default function ReportsPage() {
  const { data: pastReports, isLoading, refetch } = useReports();
  const [streamingText, setStreamingText] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    setStreaming(true);
    setStreamingText("");
    setError(null);

    await streamSSE(
      "/reports/weekly",
      { period_days: 7 },
      {
        onToken: (text) => setStreamingText((prev) => prev + text),
        onError: (msg) => setError(msg),
      }
    );

    setStreaming(false);
    refetch();
  }

  return (
    <div className="px-8 py-8 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold">Weekly report</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Generated on demand from the last 7 days of imported activity.
          </p>
        </div>
        <Button onClick={generate} disabled={streaming}>
          {streaming ? (
            <>
              <Loader2 size={14} className="animate-spin" /> Generating
            </>
          ) : (
            <>
              <Sparkles size={14} /> Generate report
            </>
          )}
        </Button>
      </div>

      {error && <p className="mt-4 text-sm text-destructive">{error}</p>}

      {(streamingText || streaming) && (
        <Card className="mt-6">
          <CardContent className="pt-5">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{streamingText}</p>
          </CardContent>
        </Card>
      )}

      <div className="mt-8">
        <h2 className="text-sm font-medium text-muted-foreground">Past reports</h2>
        <div className="mt-3 space-y-3">
          {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
          {!isLoading && (pastReports?.length ?? 0) === 0 && (
            <p className="text-sm text-muted-foreground">No reports generated yet.</p>
          )}
          {pastReports?.map((r) => (
            <Card key={r.id}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <ScrollText size={14} />
                  {format(new Date(r.period_start), "MMM d")} -- {format(new Date(r.period_end), "MMM d, yyyy")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{r.content}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
