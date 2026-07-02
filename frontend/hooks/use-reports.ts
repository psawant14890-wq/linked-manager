import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ApiResponse, WeeklyReport } from "@/lib/types";

export function useReports() {
  return useQuery({
    queryKey: ["reports"],
    queryFn: async () => {
      const res = await apiClient.get<ApiResponse<WeeklyReport[]>>("/reports");
      return res.data.data ?? [];
    },
  });
}
