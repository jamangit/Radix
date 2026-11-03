"use client";

import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { logout } from "@/lib/api/auth";
import { useCurrentUser } from "../use-current-user";

export function UserMenu() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: user } = useCurrentUser();

  const mutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(["me"], null);
      router.replace("/login");
    },
  });

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-muted-foreground">{user?.name}</span>
      <Button
        variant="outline"
        size="sm"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
      >
        Sign out
      </Button>
    </div>
  );
}