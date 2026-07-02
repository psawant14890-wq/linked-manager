"use client";

import axios from "axios";
import { CheckCircle2, FileWarning, Upload, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import type { ImportSummary } from "@/lib/types";

const STATUS_ICON = {
  success: <CheckCircle2 className="text-priority-collaboration" size={16} />,
  partial: <FileWarning className="text-priority-recruiter" size={16} />,
  failed: <XCircle className="text-priority-spam" size={16} />,
};

export default function ImportPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [summary, setSummary] = useState<ImportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setUploading(true);
    setError(null);
    setSummary(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await apiClient.post("/import", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setSummary(res.data.data as ImportSummary);
    } catch (err) {
      const message = axios.isAxiosError(err) ? err.response?.data?.detail ?? err.message : "Upload failed";
      setError(message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="font-display text-2xl font-semibold">Import your LinkedIn data</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Go to LinkedIn → Settings & Privacy → Data privacy → Get a copy of your data, request the full
        export, and upload the resulting zip (or individual CSVs) here. This never touches LinkedIn&apos;s API
        directly -- it only reads the export LinkedIn already gives you.
      </p>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Upload export</CardTitle>
          <CardDescription>Accepts a .zip from LinkedIn&apos;s export, or individual Messages/Shares/Connections .csv files.</CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className="flex flex-col items-center justify-center gap-3 rounded-md border border-dashed border-border bg-muted/40 px-6 py-10 text-center cursor-pointer hover:bg-muted/60 transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={28} className="text-muted-foreground" />
            <p className="text-sm font-medium">Click to choose a file</p>
            <p className="text-xs text-muted-foreground">.zip or .csv, up to 25MB</p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".zip,.csv"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFile(file);
              }}
            />
          </div>

          {uploading && <p className="mt-4 text-sm text-muted-foreground">Parsing your export...</p>}
          {error && <p className="mt-4 text-sm text-destructive">{error}</p>}

          {summary && (
            <div className="mt-6 space-y-4">
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="rounded-md border border-border p-3">
                  <p className="font-data text-xl font-semibold">{summary.total_messages_imported}</p>
                  <p className="text-xs text-muted-foreground">Messages</p>
                </div>
                <div className="rounded-md border border-border p-3">
                  <p className="font-data text-xl font-semibold">{summary.total_posts_imported}</p>
                  <p className="text-xs text-muted-foreground">Posts</p>
                </div>
                <div className="rounded-md border border-border p-3">
                  <p className="font-data text-xl font-semibold">{summary.total_connections_imported}</p>
                  <p className="text-xs text-muted-foreground">Connections</p>
                </div>
              </div>

              <div className="space-y-2">
                {summary.files.map((f) => (
                  <div key={f.filename} className="flex items-start gap-2 rounded-md border border-border p-3 text-sm">
                    {STATUS_ICON[f.status]}
                    <div className="flex-1">
                      <p className="font-medium">{f.filename}</p>
                      <p className="text-xs text-muted-foreground">{f.rows_imported} rows imported</p>
                      {f.errors.length > 0 && (
                        <ul className="mt-1 list-disc pl-4 text-xs text-muted-foreground">
                          {f.errors.slice(0, 3).map((e, i) => (
                            <li key={i}>{e}</li>
                          ))}
                          {f.errors.length > 3 && <li>+{f.errors.length - 3} more</li>}
                        </ul>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <Button onClick={() => router.push("/dashboard")} className="w-full">
                Go to dashboard
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
