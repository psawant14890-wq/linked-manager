import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ApiResponse, Message } from "@/lib/types";

export function useMessages(params?: { category?: string; min_priority?: number }) {
  return useQuery({
    queryKey: ["messages", params],
    queryFn: async () => {
      const res = await apiClient.get<ApiResponse<Message[]>>("/messages", { params });
      return res.data.data ?? [];
    },
  });
}
