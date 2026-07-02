"use client";

import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAnalytics } from "@/hooks/use-analytics";

const CATEGORY_COLOR: Record<string, string> = {
  recruiter: "hsl(35 64% 46%)",
  collaboration: "hsl(168 32% 35%)",
  genuine: "hsl(225 40% 29%)",
  general: "hsl(36 8% 58%)",
  spam: "hsl(8 50% 48%)",
  uncategorized: "hsl(36 8% 70%)",
};

export default function AnalyticsPage() {
  const { data, isLoading } = useAnalytics();

  if (isLoading) {
    return (
      <div className="px-8 py-8">
        <p className="text-sm text-muted-foreground">Loading analytics...</p>
      </div>
    );
  }

  if (!data || (data.total_posts === 0 && data.total_messages === 0)) {
    return (
      <div className="px-8 py-8 max-w-3xl">
        <h1 className="font-display text-2xl font-semibold">Analytics</h1>
        <p className="mt-4 text-sm text-muted-foreground">
          No data yet. Import your LinkedIn export to see posting frequency, top posts, and message
          breakdowns. If your export didn&apos;t include post-level view/like counts, you can also upload
          LinkedIn&apos;s separate post-analytics CSV from your account&apos;s analytics export.
        </p>
      </div>
    );
  }

  return (
    <div className="px-8 py-8 max-w-5xl">
      <h1 className="font-display text-2xl font-semibold">Analytics</h1>
      <p className="mt-1 text-sm text-muted-foreground">Posting cadence, top performers, and inbox breakdown.</p>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Posting frequency</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            {data.posting_frequency.length === 0 ? (
              <p className="text-sm text-muted-foreground">No dated posts found.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.posting_frequency}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="period" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", fontSize: 12 }}
                  />
                  <Bar dataKey="post_count" fill="hsl(225 40% 29%)" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Message category breakdown</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            {data.category_breakdown.length === 0 ? (
              <p className="text-sm text-muted-foreground">No classified messages yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.category_breakdown}
                    dataKey="count"
                    nameKey="category"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                  >
                    {data.category_breakdown.map((entry) => (
                      <Cell key={entry.category} fill={CATEGORY_COLOR[entry.category] ?? "hsl(36 8% 58%)"} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", fontSize: 12 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
            <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
              {data.category_breakdown.map((c) => (
                <div key={c.category} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: CATEGORY_COLOR[c.category] ?? "hsl(36 8% 58%)" }}
                  />
                  {c.category} ({c.count})
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Top performing posts</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {data.top_posts.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No view/like data found in your export -- upload a post-analytics CSV to populate this.
            </p>
          ) : (
            data.top_posts.map((p, i) => (
              <div key={i} className="rounded-md border border-border p-3">
                <p className="text-sm">{p.content}</p>
                <div className="mt-2 flex gap-4 font-data text-xs text-muted-foreground">
                  <span>{p.views ?? 0} views</span>
                  <span>{p.likes ?? 0} likes</span>
                  <span>{p.comments ?? 0} comments</span>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
