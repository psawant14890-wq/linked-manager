import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { AnalyticsResponse, ApiResponse } from "@/lib/types";

export function useAnalytics() {
  return useQuery({
    queryKey: ["analytics"],
    queryFn: async () => {
      const res = await apiClient.get<ApiResponse<AnalyticsResponse>>("/analytics");
      return res.data.data;
    },
  });
}
