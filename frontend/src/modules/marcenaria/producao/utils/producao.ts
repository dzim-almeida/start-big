/**
 * @fileoverview Regras de TELA da produção (Spec 12B). A regra de negócio
 * está no backend (12A); aqui só se decide o que mostrar e se aplica a
 * marcação otimista (D11) do mesmo jeito que o backend aplicaria.
 */
import { parseDataPura } from '@/shared/utils/date.utils';

import type { Etapa, MovelProducao, ProducaoDaOS, StatusEtapa } from '../schemas/producao.schema';

/** Um funcionário para o "Feito por" e o "Iniciar" (D6). */
export interface OpcaoFuncionario {
  id: number;
  nome: string;
}

/** As etapas do móvel na ordem dele (a API já manda em ordem; isto garante). */
export function etapasEmOrdem(movel: MovelProducao): Etapa[] {
  return [...(movel.etapas ?? [])].sort((a, b) => a.ordem - b.ordem);
}

/** A próxima etapa do móvel: a primeira ainda não concluída (12A D10). */
export function proximaEtapa(movel: MovelProducao): Etapa | null {
  return etapasEmOrdem(movel).find((e) => e.status !== 'CONCLUIDA') ?? null;
}

/** Um botão do "Concluir em todos" (D2): o nome, as etapas pendentes e em quantos móveis. */
export interface EtapaEmLote {
  nome: string;
  etapaIds: number[];
}

/**
 * D2: um botão por etapa que ainda tem pendência, na ordem em que as etapas
 * aparecem nos móveis. O nome não diferencia maiúsculas ("Corte" = "corte"),
 * como o backend (12A D11).
 */
export function etapasParaConcluirEmTodos(moveis: MovelProducao[]): EtapaEmLote[] {
  const porNome = new Map<string, EtapaEmLote>();
  for (const movel of moveis) {
    for (const etapa of etapasEmOrdem(movel)) {
      const chave = etapa.nome.toLocaleLowerCase('pt-BR');
      if (!porNome.has(chave)) porNome.set(chave, { nome: etapa.nome, etapaIds: [] });
      if (etapa.status !== 'CONCLUIDA') porNome.get(chave)!.etapaIds.push(etapa.id);
    }
  }
  return [...porNome.values()].filter((grupo) => grupo.etapaIds.length > 0);
}

/** Dias de hoje até a data (negativo = já passou). */
export function diasAte(dataPura: string, hoje = new Date()): number {
  const alvo = parseDataPura(dataPura);
  const inicioDeHoje = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  return Math.round((alvo.getTime() - inicioDeHoje.getTime()) / 86_400_000);
}

/** "05/11" (sem o ano: é sempre a obra deste ano ou do próximo). */
export const diaMes = (dataPura: string) => {
  const d = parseDataPura(dataPura);
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`;
};

/** D2: "faltam 12 dias", "é hoje" ou "5 dias atrasada" (com o aviso de atraso). */
export function prazoDaEntrega(dataPura: string, hoje = new Date()): { texto: string; atrasada: boolean } {
  const dias = diasAte(dataPura, hoje);
  if (dias > 1) return { texto: `faltam ${dias} dias`, atrasada: false };
  if (dias === 1) return { texto: 'falta 1 dia', atrasada: false };
  if (dias === 0) return { texto: 'é hoje', atrasada: false };
  return { texto: `${-dias} ${dias === -1 ? 'dia atrasada' : 'dias atrasada'}`, atrasada: true };
}

/**
 * D11: a marcação aparece na tela ANTES da resposta. Devolve uma CÓPIA da
 * produção com as etapas no status novo e o progresso refeito (a resposta do
 * servidor substitui tudo logo depois).
 */
export function marcarLocalmente(
  producao: ProducaoDaOS, etapaIds: number[], status: StatusEtapa, responsavel: string | null = null,
): ProducaoDaOS {
  const alvo = new Set(etapaIds);
  const copia: ProducaoDaOS = structuredClone(producao);
  for (const movel of copia.moveis) {
    if (!movel.etapas) continue;                            // terceirizado: não tem etapas
    for (const etapa of movel.etapas) {
      if (!alvo.has(etapa.id)) continue;
      // Concluir uma concluída não muda nada (como no backend); iniciar só vale do pendente.
      if (status === 'CONCLUIDA' && etapa.status === 'CONCLUIDA') continue;
      if (status === 'EM_EXECUCAO' && etapa.status !== 'PENDENTE') continue;
      etapa.status = status;
      if (status === 'PENDENTE') etapa.responsavel = null;  // reabrir limpa o responsável
      else if (!etapa.responsavel) etapa.responsavel = responsavel;
    }
    const proxima = proximaEtapa(movel);
    movel.proxima_etapa = proxima?.nome ?? null;
    movel.pronto = movel.etapas.length > 0 && !proxima;
  }
  // O progresso do topo acompanha a marcação.
  const internas = copia.moveis.flatMap((m) => m.etapas ?? []);
  copia.progresso.etapas_concluidas = internas.filter((e) => e.status === 'CONCLUIDA').length;
  copia.progresso.moveis_prontos = copia.moveis.filter((m) => m.pronto).length;
  copia.producao_concluida = copia.moveis.length > 0 && copia.progresso.moveis_prontos === copia.moveis.length;
  copia.sugestao_status = null;                             // a sugestão é só do servidor
  return copia;
}
