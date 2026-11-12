/**
 * Abertura de uma lavagem pela comanda (Spec 03B do lava-rápido).
 *
 * Usa as rotas de SEMPRE — `POST /clientes/cliente_pf`, `POST /ordens-servico`,
 * fotos e lavadores — sem rota nova (Spec 03A). Tem payload próprio, e não o
 * schema do formulário de OS, porque aquele exige técnico e a comanda abre
 * sem responsável quando ninguém foi escolhido.
 */
import { z } from 'zod';

import api from '@/api/axios';
import { uploadFotoOS } from '@/modules/order-service/ordens/services/relationship/osPhotoMutate.service';

import { definirLavadores } from '../../shared/services/patio.service';

export interface ClienteNovo {
  nome: string;
  celular: string;
}

export interface ItemComanda {
  servico_id: number;
  nome: string;
  /** Centavos. */
  valor: number;
}

export interface PayloadLavagem {
  cliente_id: number;
  funcionario_id: number | null;
  prioridade?: string;
  tipo_veiculo: string;
  placa: string;
  modelo: string;
  marca: string;
  cor: string;
  /** Dados do veículo que já existiam (segunda visita): o porte é sobrescrito. */
  dados_objeto: Record<string, unknown>;
  porte: string;
  itens: ItemComanda[];
  /**
   * Itens do modal de item da OS (produto do estoque ou serviço avulso), já no
   * formato do `POST /ordens-servico` (Spec 03B, revisão de 12/11).
   */
  extras?: Record<string, unknown>[];
  avarias: string[];
  observacao: string;
  /** Instante calculado, ou o dia "AAAA-MM-DD" escolhido à mão (como na OS). */
  previsao: Date | string | null;
  /** Resumo da OS (centavos): adiantamento, forma dele e deslocamento. */
  valor_entrada?: number;
  forma_pagamento_entrada_id?: number | null;
  taxa_entrega?: number;
}

/** Cliente novo só com nome e celular (CPF é opcional no cadastro). */
export async function criarClienteRapido(cliente: ClienteNovo): Promise<number> {
  const { data } = await api.post('/clientes/cliente_pf', {
    tipo: 'PF',
    nome: cliente.nome.trim(),
    celular: cliente.celular.replace(/\D/g, '') || null,
  });
  return z.object({ id: z.number() }).parse(data).id;
}

/** O que vai no `defeito_relatado` (obrigatório na OS): a observação ou os serviços. */
export function textoDoPedido(observacao: string, itens: ItemComanda[]): string {
  const texto = observacao.trim() || itens.map((i) => i.nome).join(', ') || 'Lavagem';
  return texto.slice(0, 500);
}

/** Monta o corpo do `POST /ordens-servico` a partir da comanda. */
export function montarOS(p: PayloadLavagem): Record<string, unknown> {
  return {
    cliente_id: p.cliente_id,
    funcionario_id: p.funcionario_id,
    prioridade: p.prioridade ?? 'NORMAL',
    defeito_relatado: textoDoPedido(p.observacao, p.itens),
    data_previsao: p.previsao instanceof Date ? p.previsao.toISOString() : (p.previsao || null),
    ...(p.valor_entrada ? { valor_entrada: p.valor_entrada, forma_pagamento_entrada_id: p.forma_pagamento_entrada_id ?? null } : {}),
    ...(p.taxa_entrega ? { taxa_entrega: p.taxa_entrega } : {}),
    dados_adicionais: {
      tipo_trabalho: p.tipo_veiculo,
      avarias: p.avarias,
      ...(p.observacao.trim() ? { pertences: p.observacao.trim() } : {}),
    },
    objeto: {
      numero_serie: p.placa,                         // vazio: o backend gera VEI-...
      modelo: p.modelo.trim(),
      marca: p.marca.trim(),
      cor: p.cor.trim(),
      dados_adicionais: { ...p.dados_objeto, porte: p.porte },
    },
    itens: [
      ...p.itens.map((item) => ({
        tipo: 'SERVICO',
        item_id: item.servico_id,
        nome: item.nome,
        unidade_medida: 'UN',
        quantidade: 1,
        valor_unitario: item.valor,
      })),
      ...(p.extras ?? []),
    ],
  };
}

/**
 * Abre a lavagem: OS, depois lavadores e fotos. Lavadores e fotos que falharem
 * NÃO desfazem a OS (ela já está no pátio): voltam como aviso.
 */
export async function abrirLavagem(
  p: PayloadLavagem,
  lavadores: number[],
  fotos: File[],
): Promise<{ numero_os: string; avisos: string[] }> {
  const { data } = await api.post('/ordens-servico/', montarOS(p));
  const numero_os = z.object({ numero_os: z.string() }).parse(data).numero_os;
  const avisos: string[] = [];

  if (lavadores.length) {
    try {
      await definirLavadores(numero_os, lavadores);
    } catch {
      avisos.push('os lavadores');
    }
  }
  for (const foto of fotos) {
    try {
      await uploadFotoOS({ osNumber: numero_os, imageFile: foto });
    } catch {
      avisos.push(`a foto ${foto.name}`);
    }
  }
  return { numero_os, avisos };
}
