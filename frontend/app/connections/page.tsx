"use client";

import { format } from "date-fns";
import { Building2, Search, Users } from "lucide-react";
import { useState } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useConnectionSearch } from "@/hooks/use-jobs-and-connections";

const EXAMPLE_QUERIES = [
  "machine learning engineers at FAANG",
  "VCs in fintech",
  "design leaders in Europe",
  "startup founders in SaaS",
  "engineering managers at Series B",
];

export default function ConnectionsPage() {
  const [query, setQuery] = useState("");
  const { data: results = [], isLoading, isFetching } = useConnectionSearch(query);

  return (
    <div className="px-8 py-8 max-w-3xl">
      <h1 className="font-display text-2xl font-semibold">Search your network</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Ask in plain English. Searches across name, title, and company using semantic similarity —
        not just exact keyword matching.
      </p>

      <div className="relative mt-6">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-9 h-10"
          placeholder="e.g. machine learning engineers at FAANG"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {!query && (
        <div className="mt-4 flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              onClick={() => setQuery(q)}
              className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {query && (isLoading || isFetching) && (
        <p className="mt-6 text-sm text-muted-foreground">Searching...</p>
      )}

      {query && !isLoading && !isFetching && results.length === 0 && (
        <div className="mt-6 rounded-md border border-dashed border-border p-6 text-center">
          <Users size={24} className="mx-auto mb-2 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            No matching connections found. Try a different query, or import your Connections.csv
            if you haven&apos;t yet.
          </p>
        </div>
      )}

      {results.length > 0 && (
        <div className="mt-6 space-y-2">
          <p className="text-xs text-muted-foreground">
            {results.length} result{results.length !== 1 ? "s" : ""} closest to &ldquo;{query}&rdquo;
          </p>
          {results.map((c) => (
            <Card key={c.id}>
              <CardContent className="flex items-center gap-3 py-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-muted font-medium text-sm text-muted-foreground">
                  {c.name.slice(0, 2).toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">{c.name}</p>
                  {(c.title || c.company) && (
                    <p className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5 truncate">
                      {c.title}
                      {c.title && c.company && " · "}
                      {c.company && (
                        <>
                          <Building2 size={10} className="shrink-0" />
                          {c.company}
                        </>
                      )}
                    </p>
                  )}
                </div>
                {c.connected_at && (
                  <p className="shrink-0 font-data text-xs text-muted-foreground">
                    {format(new Date(c.connected_at), "MMM yyyy")}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
