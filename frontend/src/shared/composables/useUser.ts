import { useQuery } from "@tanstack/vue-query";
import { getUser } from "../services/user.service";
import { TOKEN_KEY } from "@/api/axios";

export function useUserQuery() {
    return useQuery({
        queryKey: ['user-me'],
        queryFn: () => getUser(),
        enabled: () => !!localStorage.getItem(TOKEN_KEY),
        staleTime: 1000 * 60 * 30
    });
}