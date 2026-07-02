import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ApiResponse, UserProfile } from "@/lib/types";

export function useUserProfile() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const res = await apiClient.get<ApiResponse<UserProfile>>("/auth/me");
      return res.data.data;
    },
  });
}

export function useUpdateBioContext() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (bio_context: string) => {
      const res = await apiClient.patch<ApiResponse<UserProfile>>("/auth/me/bio-context", { bio_context });
      return res.data.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["me"] }),
  });
}
