/**
 * @fileoverview Textos e regras de TELA da entrega (Spec 13B). A regra de
 * negócio é do backend (13A); aqui só se decide o que mostrar.
 */
import { parseDataPura } from '@/shared/utils/date.utils';
import { diaMes } from '@/modules/marcenaria/producao/utils/producao';
import { hojeIso } from '@/modules/marcenaria/terceirizados/utils/terceirizados';

import type { Agendamento, EntregaAmbiente, Instalacao, ResumoEntrega, SituacaoEntrega } from '../schemas/entrega.schema';

/** A situação como o usuário lê, e a cor do selo (13B D3). */
export const ROTULO_SITUACAO_ENTREGA: Record<SituacaoEntrega, string> = {
  PENDENTE: 'Pendente',
  CONFORME: 'Conforme',
  COM_RESSALVAS: 'Com ressalvas',
};
export const CLASSE_SITUACAO_ENTREGA: Record<SituacaoEntrega, string> = {
  PENDENTE: 'bg-zinc-100 text-zinc-700 border-zinc-200',
  CONFORME: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  COM_RESSALVAS: 'bg-amber-50 text-amber-800 border-amber-200',
};

/** Plural simples: "1 ambiente" / "3 ambientes". */
const plural = (n: number, um: string, varios: string) => `${n} ${n === 1 ? um : varios}`;

/** D2: "1 de 3 ambientes entregues · 2 pendências abertas". */
export function textoDoResumo(resumo: ResumoEntrega): string {
  const base = `${resumo.entregues} de ${plural(resumo.total, 'ambiente entregue', 'ambientes entregues')}`;
  const abertas = resumo.pendencias_abertas.length;
  return abertas ? `${base} · ${plural(abertas, 'pendência aberta', 'pendências abertas')}` : base;
}

/** "Carlos, Davi". */
export const nomesDosMontadores = (montadores: { nome: string }[]) => montadores.map((m) => m.nome).join(', ');

/** D3: "Instalação 03/11 às 08:00 · Carlos, Davi". */
export function textoDoAgendamento(agendamento: { data: string; hora_inicio: string | null; montadores: { nome: string }[] }): string {
  const hora = agendamento.hora_inicio ? ` às ${agendamento.hora_inicio}` : '';
  const quem = agendamento.montadores.length ? ` · ${nomesDosMontadores(agendamento.montadores)}` : '';
  return `Instalação ${diaMes(agendamento.data)}${hora}${quem}`;
}

/** D3: as marcações do checklist resumidas: "12 ok · 1 não ok" (o que ficou em branco não entra). */
export function resumoDoChecklist(checklist: EntregaAmbiente['checklist']): string {
  const ok = checklist.filter((i) => i.marcacao === 'ok').length;
  const nao = checklist.filter((i) => i.marcacao === 'nao_ok').length;
  if (!ok && !nao) return 'sem marcações';
  return [ok ? `${ok} ok` : '', nao ? `${nao} não ok` : ''].filter(Boolean).join(' · ');
}

/** As fotos escolhidas no modal de registro (sobem ANTES do registro, 13A D8). */
export interface FotosDoRegistro {
  termo: File | null;
  montagem: File[];
}

/** O ambiente já teve o termo passado a limpo (Conforme ou Com ressalvas)? */
export const registrada = (entrega: EntregaAmbiente) => entrega.situacao !== 'PENDENTE';

/** Os ambientes que um agendamento pode ter: os pendentes, e os que ele já tinha (ao editar). */
export function ambientesAgendaveis(entregas: EntregaAmbiente[], agendamento: Agendamento | null): EntregaAmbiente[] {
  const doAgendamento = new Set(agendamento?.ambiente_ids ?? []);
  return entregas.filter((e) => !registrada(e) || doAgendamento.has(e.ambiente_id));
}

// --- Nome sugerido do PDF (D14, como a proposta da 07) --------------------------------

/** Caracteres proibidos em nome de arquivo no Windows. */
const PROIBIDOS = /[\\/:*?"<>|]/g;
const limpo = (texto: string) => texto.replace(PROIBIDOS, ' ').replace(/\s+/g, ' ').trim().slice(0, 60).trim();

/** "Termo OS-2026-000512 - Cozinha Gourmet". */
export const nomeArquivoTermo = (numeroOs: string, ambiente: string) => `Termo ${numeroOs} - ${limpo(ambiente)}`;

/** "Termos OS-2026-000512 - 03-11-2026" (a barra da data não pode estar no nome do arquivo). */
export function nomeArquivoTermos(numeroOs: string, dataPura: string): string {
  const [ano, mes, dia] = dataPura.split('-');
  return `Termos ${numeroOs} - ${dia}-${mes}-${ano}`;
}

// --- Aba Instalações (D16) ----------------------------------------------------------------

export type Periodo = 'hoje' | 'amanha' | 'semana' | 'proximos30';
export const PERIODOS: { id: Periodo; rotulo: string }[] = [
  { id: 'hoje', rotulo: 'Hoje' },
  { id: 'amanha', rotulo: 'Amanhã' },
  { id: 'semana', rotulo: 'Esta semana' },
  { id: 'proximos30', rotulo: 'Próximos 30 dias' },
];

/** Soma dias a uma data (no relógio da loja). */
function maisDias(data: Date, dias: number): Date {
  const copia = new Date(data.getFullYear(), data.getMonth(), data.getDate());
  copia.setDate(copia.getDate() + dias);
  return copia;
}

/**
 * O período do atalho em datas puras ("2026-11-03"). "Esta semana" vai de
 * segunda a domingo da semana de hoje (o que já passou nela também aparece).
 */
export function datasDoPeriodo(periodo: Periodo, hoje = new Date()): { de: string; ate: string } {
  if (periodo === 'hoje') return { de: hojeIso(hoje), ate: hojeIso(hoje) };
  if (periodo === 'amanha') {
    const amanha = maisDias(hoje, 1);
    return { de: hojeIso(amanha), ate: hojeIso(amanha) };
  }
  if (periodo === 'semana') {
    const desdeSegunda = (hoje.getDay() + 6) % 7;          // getDay(): 0 = domingo
    const segunda = maisDias(hoje, -desdeSegunda);
    return { de: hojeIso(segunda), ate: hojeIso(maisDias(segunda, 6)) };
  }
  return { de: hojeIso(hoje), ate: hojeIso(maisDias(hoje, 30)) };
}

const DIAS_DA_SEMANA = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'];

/** "Segunda, 03/11". */
export function tituloDoDia(dataPura: string): string {
  return `${DIAS_DA_SEMANA[parseDataPura(dataPura).getDay()]}, ${diaMes(dataPura)}`;
}

/** D16: a lista agrupada por dia, na ordem que a API manda (data e hora). */
export function agruparPorDia(itens: Instalacao[]): { data: string; titulo: string; itens: Instalacao[] }[] {
  const grupos = new Map<string, Instalacao[]>();
  for (const item of itens) {
    if (!grupos.has(item.data)) grupos.set(item.data, []);
    grupos.get(item.data)!.push(item);
  }
  return [...grupos.entries()].map(([data, doDia]) => ({ data, titulo: tituloDoDia(data), itens: doDia }));
}

/** Os montadores que aparecem na lista (o filtro não precisa buscar funcionários). */
export function montadoresDaLista(itens: Instalacao[]): { funcionario_id: number; nome: string }[] {
  const vistos = new Map<number, string>();
  for (const item of itens) for (const m of item.montadores) vistos.set(m.funcionario_id, m.nome);
  return [...vistos.entries()]
    .map(([funcionario_id, nome]) => ({ funcionario_id, nome }))
    .sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));
}
