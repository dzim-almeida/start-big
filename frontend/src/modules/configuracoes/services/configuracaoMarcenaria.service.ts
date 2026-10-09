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
