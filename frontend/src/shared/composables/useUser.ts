import { useQuery } from "@tanstack/vue-query";
import { getUser } from "../services/user.service";

export function useUserQuery() {
    return useQuery({
        queryKey: ['user-me'],
        queryFn: () => getUser(),
        staleTime: 1000 * 60 * 30
    });
}