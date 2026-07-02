import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ApiResponse } from "@/lib/types";

export type JobStatus = "new" | "interested" | "applied" | "declined";

export type JobOpportunity = {
  id: string;
  message_id: string;
  sender_name: string | null;
  company: string | null;
  role_title: string | null;
  seniority: string | null;
  location: string | null;
  remote_policy: string | null;
  salary_range: string | null;
  status: JobStatus;
  notes: string | null;
  extracted_at: string;
};

export function useJobs(status?: JobStatus) {
  return useQuery({
    queryKey: ["jobs", status],
    queryFn: async () => {
      const res = await apiClient.get<ApiResponse<JobOpportunity[]>>("/jobs", {
        params: status ? { job_status: status } : undefined,
      });
      return res.data.data ?? [];
    },
  });
}

export function useExtractJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (messageId: string) => {
      const res = await apiClient.post<ApiResponse<JobOpportunity>>(`/jobs/extract/${messageId}`);
      return res.data.data!;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

export function useUpdateJobStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ jobId, status }: { jobId: string; status: JobStatus }) => {
      const res = await apiClient.patch<ApiResponse<JobOpportunity>>(`/jobs/${jobId}/status`, { status });
      return res.data.data!;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

export function useUpdateJobNotes() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ jobId, notes }: { jobId: string; notes: string }) => {
      const res = await apiClient.patch<ApiResponse<JobOpportunity>>(`/jobs/${jobId}/notes`, { notes });
      return res.data.data!;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

// --- Connections ---

export type Connection = {
  id: string;
  name: string;
  company: string | null;
  title: string | null;
  connected_at: string | null;
};

export function useConnectionSearch(query: string) {
  return useQuery({
    queryKey: ["connections", "search", query],
    queryFn: async () => {
      if (!query.trim()) return [];
      const res = await apiClient.get<ApiResponse<Connection[]>>("/connections/search", {
        params: { q: query },
      });
      return res.data.data ?? [];
    },
    enabled: query.trim().length >= 2,
  });
}

// --- Follow-up flagging ---

export type FollowUpMessage = {
  id: string;
  sender_name: string;
  content: string;
  category: string | null;
  priority_score: number | null;
  summary: string | null;
  received_at: string | null;
  is_actioned: boolean;
};

export function useFollowUps(days = 3) {
  return useQuery({
    queryKey: ["follow-ups", days],
    queryFn: async () => {
      const res = await apiClient.get<ApiResponse<FollowUpMessage[]>>("/messages/follow-ups", {
        params: { days },
      });
      return res.data.data ?? [];
    },
  });
}

export function useMarkActioned() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (messageId: string) => {
      await apiClient.post(`/messages/${messageId}/mark-actioned`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["follow-ups"] });
      qc.invalidateQueries({ queryKey: ["messages"] });
    },
  });
}
