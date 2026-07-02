"use client";

import Link from "next/link";

import { FollowUpWidget } from "@/components/layout/follow-up-widget";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CategoryBadge } from "@/components/ui/category-badge";
import { useAnalytics } from "@/hooks/use-analytics";
import { useJobs } from "@/hooks/use-jobs-and-connections";
import { useMessages } from "@/hooks/use-messages";

export default function DashboardPage() {
  const { data: analytics, isLoading: analyticsLoading } = useAnalytics();
  const { data: messages, isLoading: messagesLoading } = useMessages({ min_priority: 55 });
  const { data: jobs = [] } = useJobs();

  const activeJobs = jobs.filter((j) => j.status !== "declined");

  return (
    <div className="px-8 py-8 max-w-5xl">
      <h1 className="font-display text-2xl font-semibold">Dashboard</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        A snapshot of your inbox and posting activity.
      </p>

      {/* Stat row */}
      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card>
          <CardHeader className="pb-1">
            <CardTitle className="text-xs font-medium text-muted-foreground">Total messages</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-data text-3xl font-semibold">
              {analyticsLoading ? "--" : (analytics?.total_messages ?? 0)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-1">
            <CardTitle className="text-xs font-medium text-muted-foreground">Posts published</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-data text-3xl font-semibold">
              {analyticsLoading ? "--" : (analytics?.total_posts ?? 0)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-1">
            <CardTitle className="text-xs font-medium text-muted-foreground">Avg. views</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-data text-3xl font-semibold">
              {analyticsLoading
                ? "--"
                : analytics?.avg_views
                ? Math.round(analytics.avg_views)
                : "N/A"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-1">
            <CardTitle className="text-xs font-medium text-muted-foreground">Active opportunities</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-data text-3xl font-semibold">{activeJobs.length}</p>
          </CardContent>
        </Card>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* High-priority messages */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">High-priority messages</CardTitle>
            <Link href="/inbox" className="text-xs text-primary underline-offset-4 hover:underline">
              View inbox
            </Link>
          </CardHeader>
          <CardContent className="space-y-2">
            {messagesLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
            {!messagesLoading && (messages?.length ?? 0) === 0 && (
              <p className="text-sm text-muted-foreground">
                Nothing high-priority yet. Import your data or check the full inbox.
              </p>
            )}
            {messages?.slice(0, 5).map((m) => (
              <div
                key={m.id}
                className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{m.sender_name}</p>
                  <p className="truncate text-xs text-muted-foreground">
                    {m.summary ?? m.content}
                  </p>
                </div>
                <CategoryBadge category={m.category} />
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Follow-up widget */}
        <FollowUpWidget />
      </div>

      {/* Active job opportunities snapshot */}
      {activeJobs.length > 0 && (
        <Card className="mt-4">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Active opportunities</CardTitle>
            <Link href="/jobs" className="text-xs text-primary underline-offset-4 hover:underline">
              View pipeline
            </Link>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {activeJobs.slice(0, 6).map((job) => (
                <div
                  key={job.id}
                  className="rounded-md border border-border px-3 py-2"
                >
                  <p className="truncate text-sm font-medium">
                    {job.role_title ?? "Unknown role"}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">
                    {job.company ?? "Unknown company"}
                    {job.remote_policy && ` · ${job.remote_policy}`}
                  </p>
                  <p className="mt-1 text-xs capitalize text-muted-foreground">{job.status}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
