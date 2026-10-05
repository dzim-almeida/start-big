/**
 * @fileoverview API da marcenaria-fábrica (/fabrica).
 *
 * Toda rota daqui responde 403 `SEGMENTO_SEM_FABRICA` fora do segmento
 * Marcenaria — quem chama já deve ter conferido `isMarcenaria`.
 */

import api from '@/api/axios';
import type {
  InsumoBusca,
  InsumoEscrita,
  InsumoRead,
  OrcamentoEscrita,
  OrcamentoRead,
  OrcamentoResumo,
  TrilhoRead,
  SeparacaoRead,
  MargemRead,
  PedidoServicoEscrita,
  PedidoServicoRead,
} from '../types/fabrica.types';

export async function getInsumo(produtoId: number): Promise<InsumoRead> {
  const { data } = await api.get<InsumoRead>(`fabrica/produtos/${produtoId}/insumo`);
  return data;
}

export async function salvarInsumo(produtoId: number, insumo: InsumoEscrita): Promise<InsumoRead> {
  const { data } = await api.put<InsumoRead>(`fabrica/produtos/${produtoId}/insumo`, insumo);
  return data;
}

// --- F2: orçamento por móvel --------------------------------------------------

export async function buscarInsumos(busca: string): Promise<InsumoBusca[]> {
  const { data } = await api.get<InsumoBusca[]>('fabrica/insumos', { params: { busca } });
  return data;
}

export async function listarOrcamentos(numeroOs: string): Promise<OrcamentoResumo[]> {
  const { data } = await api.get<OrcamentoResumo[]>(`fabrica/os/${numeroOs}/orcamentos`);
  return data;
}

/** Nova versão: vazia, ou cópia de `copiarDe` (desta mesma OS). */
export async function criarOrcamento(numeroOs: string, copiarDe?: number): Promise<OrcamentoRead> {
  const { data } = await api.post<OrcamentoRead>(`fabrica/os/${numeroOs}/orcamentos`, {
    copiar_de: copiarDe ?? null,
  });
  return data;
}

export async function getOrcamento(id: number): Promise<OrcamentoRead> {
  const { data } = await api.get<OrcamentoRead>(`fabrica/orcamentos/${id}`);
  return data;
}

/** A árvore inteira (só RASCUNHO): o que não vier sai. */
export async function salvarOrcamento(id: number, orcamento: OrcamentoEscrita): Promise<OrcamentoRead> {
  const { data } = await api.put<OrcamentoRead>(`fabrica/orcamentos/${id}`, orcamento);
  return data;
}

export async function enviarOrcamento(id: number): Promise<OrcamentoRead> {
  const { data } = await api.post<OrcamentoRead>(`fabrica/orcamentos/${id}/enviar`);
  return data;
}

export async function aprovarOrcamento(id: number): Promise<OrcamentoRead> {
  const { data } = await api.post<OrcamentoRead>(`fabrica/orcamentos/${id}/aprovar`);
  return data;
}

export async function recusarOrcamento(id: number, motivo: string): Promise<OrcamentoRead> {
  const { data } = await api.post<OrcamentoRead>(`fabrica/orcamentos/${id}/recusar`, { motivo });
  return data;
}

// --- F3: o trilho ----------------------------------------------------------------

export async function getTrilho(numeroOs: string): Promise<TrilhoRead> {
  const { data } = await api.get<TrilhoRead>(`fabrica/os/${numeroOs}/trilho`);
  return data;
}

/** 422 MOTIVO_OBRIGATORIO / 409 TRAVA_PENDENTE quando há pendência (ver o backend). */
export async function avancarEtapa(numeroOs: string, motivo?: string): Promise<TrilhoRead> {
  const { data } = await api.post<TrilhoRead>(`fabrica/os/${numeroOs}/avancar`, { motivo: motivo ?? null });
  return data;
}

export async function voltarEtapa(numeroOs: string, fase: string, motivo: string): Promise<TrilhoRead> {
  const { data } = await api.post<TrilhoRead>(`fabrica/os/${numeroOs}/voltar`, { fase, motivo });
  return data;
}

export async function liberarCompra(numeroOs: string, motivo: string): Promise<TrilhoRead> {
  const { data } = await api.post<TrilhoRead>(`fabrica/os/${numeroOs}/liberar-compra`, { motivo });
  return data;
}

export async function definirInstalacao(numeroOs: string, dataInstalacao: string | null): Promise<TrilhoRead> {
  const { data } = await api.put<TrilhoRead>(`fabrica/os/${numeroOs}/instalacao`, {
    data_instalacao: dataInstalacao,
  });
  return data;
}

// --- F4: separação e margem ---------------------------------------------------------

export async function getSeparacao(numeroOs: string): Promise<SeparacaoRead> {
  const { data } = await api.get<SeparacaoRead>(`fabrica/os/${numeroOs}/separacao`);
  return data;
}

/** Um bipe (`codigo`) ou um item escolhido (`itemId`). Dá a baixa na hora. */
export async function separar(
  numeroOs: string,
  alvo: { codigo?: string; itemId?: number },
  quantidade = 1,
): Promise<SeparacaoRead> {
  const { data } = await api.post<SeparacaoRead>(`fabrica/os/${numeroOs}/separacao`, {
    codigo: alvo.codigo ?? null,
    item_id: alvo.itemId ?? null,
    quantidade,
  });
  return data;
}

export async function estornarSeparacao(
  numeroOs: string,
  itemId: number,
  quantidade: number,
  motivo: string,
): Promise<SeparacaoRead> {
  const { data } = await api.post<SeparacaoRead>(`fabrica/os/${numeroOs}/separacao/estornar`, {
    item_id: itemId,
    quantidade,
    motivo,
  });
  return data;
}

export async function getMargem(numeroOs: string): Promise<MargemRead> {
  const { data } = await api.get<MargemRead>(`fabrica/os/${numeroOs}/margem`);
  return data;
}

// --- F5: central de corte -------------------------------------------------------------

export async function criarPedidoServico(movelId: number, pedido: PedidoServicoEscrita): Promise<PedidoServicoRead> {
  const { data } = await api.post<PedidoServicoRead>(`fabrica/moveis/${movelId}/pedido-servico`, pedido);
  return data;
}
