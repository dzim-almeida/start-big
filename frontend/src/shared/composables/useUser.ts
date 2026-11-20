import { useQuery } from "@tanstack/vue-query";
import { getUser } from "../services/user.service";
// Lê o token pelo dono único dele (LIC-04, D-27)
import { lerToken } from "../services/tokenSessao.service";

export function useUserQuery() {
    return useQuery({
        queryKey: ['user-me'],
        queryFn: () => getUser(),
        // Só busca o usuário quando há login nesta janela
        enabled: () => !!lerToken(),
        staleTime: 1000 * 60 * 30
    });
}