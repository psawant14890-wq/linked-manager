"use client";

import { Building2, ChevronDown, MapPin, Sparkles } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { type JobOpportunity, type JobStatus, useJobs, useUpdateJobNotes, useUpdateJobStatus } from "@/hooks/use-jobs-and-connections";
import { cn } from "@/lib/utils";

const COLUMNS: { status: JobStatus; label: string; color: string }[] = [
  { status: "new",        label: "New",        color: "hsl(var(--priority-recruiter))" },
  { status: "interested", label: "Interested", color: "hsl(var(--priority-genuine))" },
  { status: "applied",    label: "Applied",    color: "hsl(var(--priority-collaboration))" },
  { status: "declined",   label: "Declined",   color: "hsl(var(--priority-spam))" },
];

function JobCard({ job }: { job: JobOpportunity }) {
  const [expanded, setExpanded] = useState(false);
  const [notes, setNotes] = useState(job.notes ?? "");
  const updateStatus = useUpdateJobStatus();
  const updateNotes = useUpdateJobNotes();

  const otherStatuses = COLUMNS.filter((c) => c.status !== job.status);

  return (
    <div className="rounded-md border border-border bg-card text-sm">
      <button
        className="flex w-full items-start justify-between gap-2 p-3 text-left"
        onClick={() => setExpanded((e) => !e)}
      >
        <div className="min-w-0">
          <p className="font-medium truncate">{job.role_title ?? "Unknown role"}</p>
          {job.company && (
            <p className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5">
              <Building2 size={11} /> {job.company}
            </p>
          )}
        </div>
        <ChevronDown size={14} className={cn("shrink-0 mt-0.5 transition-transform text-muted-foreground", expanded && "rotate-180")} />
      </button>

      {expanded && (
        <div className="border-t border-border p-3 space-y-2">
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground">
            {job.seniority && <span>Level: {job.seniority}</span>}
            {job.remote_policy && <span>Remote: {job.remote_policy}</span>}
            {job.location && (
              <span className="flex items-center gap-1 col-span-2">
                <MapPin size={10} /> {job.location}
              </span>
            )}
            {job.salary_range && <span className="col-span-2">Salary: {job.salary_range}</span>}
            {job.sender_name && <span className="col-span-2">Recruiter: {job.sender_name}</span>}
          </div>

          <Textarea
            className="min-h-16 text-xs"
            placeholder="Your notes..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            onBlur={() => updateNotes.mutate({ jobId: job.id, notes })}
          />

          <div className="flex flex-wrap gap-1">
            {otherStatuses.map((col) => (
              <button
                key={col.status}
                onClick={() => updateStatus.mutate({ jobId: job.id, status: col.status })}
                className="rounded-full border px-2.5 py-0.5 text-xs transition-colors hover:bg-muted"
                style={{ borderColor: col.color, color: col.color }}
              >
                Move → {col.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function JobsPage() {
  const { data: jobs = [], isLoading } = useJobs();

  const byStatus = (status: JobStatus) => jobs.filter((j) => j.status === status);

  return (
    <div className="px-8 py-8">
      <div className="flex items-center justify-between mb-1">
        <h1 className="font-display text-2xl font-semibold">Job opportunities</h1>
      </div>
      <p className="text-sm text-muted-foreground mb-6">
        Extracted from recruiter messages in your inbox. Go to a recruiter message and click
        &quot;Extract opportunity&quot; to add it here.
      </p>

      {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}

      {!isLoading && jobs.length === 0 && (
        <Card className="max-w-md">
          <CardContent className="pt-5 space-y-2">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Sparkles size={16} />
              <p className="text-sm font-medium">No opportunities yet</p>
            </div>
            <p className="text-sm text-muted-foreground">
              Go to the Inbox, open a recruiter message, and click &quot;Extract opportunity&quot; to
              let GPT-4o pull out the company, role, and level automatically.
            </p>
          </CardContent>
        </Card>
      )}

      {jobs.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {COLUMNS.map((col) => (
            <div key={col.status}>
              <div className="flex items-center gap-2 mb-3">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: col.color }} />
                <h2 className="text-sm font-medium">{col.label}</h2>
                <span className="font-data text-xs text-muted-foreground ml-auto">
                  {byStatus(col.status).length}
                </span>
              </div>
              <div className="space-y-2">
                {byStatus(col.status).length === 0 && (
                  <p className="rounded-md border border-dashed border-border p-3 text-xs text-muted-foreground text-center">
                    None
                  </p>
                )}
                {byStatus(col.status).map((job) => (
                  <JobCard key={job.id} job={job} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
