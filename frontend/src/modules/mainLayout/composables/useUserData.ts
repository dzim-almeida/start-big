import { useQuery } from "@tanstack/vue-query";
import { getUserData } from "../services/layout.service";

export function useUserDataQuery(userId?: string) {
    return useQuery({
        queryKey: ['userMe', userId],
        queryFn: () => getUserData(),
        staleTime: 1000 * 60 * 60,
        retry: 1,
    });
}