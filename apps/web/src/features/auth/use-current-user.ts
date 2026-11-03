import { useQuery } from "@tanstack/react-query";
import { fetchCurrentUser } from "@/lib/api/auth";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["me"],
    queryFn: fetchCurrentUser,
    staleTime: 5 * 60_000,
    retry: false,
  });
}