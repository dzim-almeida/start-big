/**
 * Chamadas de Configurações › Marcenaria (Spec 04A/04B).
 * A resposta é conferida com zod na chegada (dois formatos, por `inclui_custos`).
 */
import api from '@/api/axios';

import {
  configuracaoMarcenariaSchema,
  type ConfiguracaoMarcenaria,
  type ConfiguracaoMarcenariaUpdate,
} from '../schemas/configuracaoMarcenaria.schema';

const URL = '/configuracoes/marcenaria';

/** Parâmetros da marcenaria (o backend cria com os padrões na primeira leitura). */
export async function getConfiguracaoMarcenaria(): Promise<ConfiguracaoMarcenaria> {
  const response = await api.get(URL);
  return configuracaoMarcenariaSchema.parse(response.data);   // formato errado vira erro da query
}

/** PUT parcial: só os campos enviados mudam. Exige `manage_custos_marcenaria`. */
export async function updateConfiguracaoMarcenaria(
  data: ConfiguracaoMarcenariaUpdate,
): Promise<ConfiguracaoMarcenaria> {
  const response = await api.put(URL, data);
  return configuracaoMarcenariaSchema.parse(response.data);
}

/**
 * Cria (ou reaproveita, pelo código) os produtos acabados "Móvel planejado" e
 * "Móvel planejado (revenda)" e os liga ao faturamento. Não liga o faturamento.
 */
export async function criarProdutosAcabados(): Promise<ConfiguracaoMarcenaria> {
  const response = await api.post(`${URL}/produtos-acabados`);
  return configuracaoMarcenariaSchema.parse(response.data);
}

/** Resposta de "dar entrada dos móveis já prontos". */
export interface SincronizacaoMoveis {
  os_conferidas: number;
  moveis_no_estoque: number;
  entraram_agora: number;
}

/**
 * Dá entrada, como produto acabado, nos móveis que já estavam prontos nas OS
 * abertas (ao ligar o faturamento com obras em andamento). Idempotente.
 */
export async function sincronizarMoveisProntos(): Promise<SincronizacaoMoveis> {
  const response = await api.post<SincronizacaoMoveis>('/marcenaria/faturamento/sincronizar');
  return response.data;
}
