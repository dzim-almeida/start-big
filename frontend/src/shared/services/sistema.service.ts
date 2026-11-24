/**
 * @fileoverview Pergunta ao backend se o sistema já foi configurado.
 *
 * "Configurado" = o setup inicial terminou e existe o usuário Master
 * (GET /auth/status → `{ inicializado }`).
 *
 * Isto NÃO é o mesmo que "tem licença". Depois do re-login (LIC-03) a licença
 * já está salva, mas a empresa e o usuário ainda não existem: a pessoa está no
 * meio do formulário. Decidir pela licença mandava essa pessoa para o login,
 * onde não há usuário para entrar (bug do build de teste, 11/2026).
 */

import axios from 'axios';
import { getApiBaseUrl } from '@/api/backendUrl';

/**
 * true = setup feito; false = falta o setup; null = não deu para perguntar
 * (backend ainda subindo, sem rede). Quem chama decide o que fazer no null.
 *
 * Usa o axios "puro" (sem o interceptor de 401) porque roda antes do login.
 */
export async function sistemaFoiConfigurado(): Promise<boolean | null> {
  try {
    const { data } = await axios.get<{ inicializado: boolean }>(`${getApiBaseUrl()}/auth/status`);
    // Só aceita um booleano de verdade; qualquer outra coisa vira "não sei".
    return typeof data?.inicializado === 'boolean' ? data.inicializado : null;
  } catch {
    return null; // erro de rede ou do backend: "não sei"
  }
}
