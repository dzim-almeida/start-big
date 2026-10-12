import type {
  OsStatusEnumDataType,
  OsPriorityEnumDataType,
  OsEquipSituacaoEnumDataType,
} from '../../ordens/schemas/enums/osEnums.schema';
import type { OsEstadoConfig } from '../../ordens/constants/ordemServico.constants';
import type { RotuloStatus } from '../segmento/segmentDefinition.type';
import { OS_ESTADO_CONFIG, OS_PRIORIDADE_OPTIONS } from '../../ordens/constants/ordemServico.constants';
import { formatData } from '@/shared/utils/date.utils';
import { formatDataPura } from '@/shared/utils/date.utils';

// Re-export shared utilities for backward compatibility
export { getClienteNome, getPaymentDisplayName, inferPaymentType, inferPermiteParcelamento } from '@/shared/utils/print.utils';

/**
 * Rótulos que o SEGMENTO declarou para a OS; todos opcionais (Spec 01B, D2).
 * Quem não passa nada (ou passa vazio) vê os textos padrão de sempre.
 */
export interface RotulosEstadoOS {
  /** Status do fluxo: `rotulos_status` do contrato (ex.: EM_ANDAMENTO -> "Em Produção"). */
  status?: Partial<Record<OsStatusEnumDataType, RotuloStatus>>;
  /** Desfecho: `rotulos_situacao` do contrato (ex.: SEM_REPARO -> "Não produzido"). */
  situacao?: Record<string, string>;
}

/**
 * Rótulo e cores do estado que a OS mostra ao usuário, cruzando o status do
 * fluxo com o desfecho do objeto.
 *
 * É por aqui que "Condenado" e "Sem Reparo" chegam à tela: eles são gravados em
 * `situacao_equipamento` e nunca aparecem em `status` (que fica FINALIZADA), então
 * ler só o status faria uma OS condenada se anunciar como "Finalizada".
 *
 * `rotulos` (opcional) troca SÓ o texto pelo que o segmento declarou; as cores
 * continuam as de OS_ESTADO_CONFIG. Sem rótulo próprio, a função devolve o
 * MESMO objeto de sempre (não uma cópia), então os outros segmentos não mudam.
 * Continua pura: quem lê o contrato é o composable `useRotulosStatusOS`.
 */
export function getEstadoOS(
  status: OsStatusEnumDataType | null | undefined,
  situacao?: OsEquipSituacaoEnumDataType | null,
  rotulos?: RotulosEstadoOS,                       // novo e opcional: sem ele, nada muda
): OsEstadoConfig {
  // O desfecho só substitui o rótulo de uma OS de fato encerrada. Reabrir NÃO
  // limpa `situacao_equipamento` (é o último desfecho conhecido do objeto), e sem
  // esta guarda uma OS reaberta continuaria se exibindo como "Condenado" enquanto
  // já está de volta à bancada.
  if (status === 'FINALIZADA' && situacao && situacao !== 'REPARADO') {
    const padraoDesfecho = OS_ESTADO_CONFIG[situacao];        // cores e texto de conserto
    const textoDesfecho = rotulos?.situacao?.[situacao];       // "Não produzido", se o segmento declarou
    // Sem rótulo do segmento: o mesmo objeto de hoje. Com rótulo: troca só o texto.
    return textoDesfecho ? { ...padraoDesfecho, label: textoDesfecho } : padraoDesfecho;
  }
  const chave = status ?? 'ABERTA';                                   // OS sem status = Aberta, como hoje
  const padrao = OS_ESTADO_CONFIG[chave] ?? OS_ESTADO_CONFIG.ABERTA;  // cores e texto padrão
  const proprio = rotulos?.status?.[chave];                           // texto do segmento, se houver
  // Copia o padrão e troca SÓ o label; as cores continuam as mesmas (D1).
  return proprio ? { ...padrao, label: proprio.rotulo } : padrao;
}

export function getPrioridadeLabel(prioridade: OsPriorityEnumDataType): string {
  const found = OS_PRIORIDADE_OPTIONS.find((p) => p.value === prioridade);
  return found?.label || prioridade;
}

export function getPrioridadeColor(prioridade: OsPriorityEnumDataType): string {
  const found = OS_PRIORIDADE_OPTIONS.find((p) => p.value === prioridade);
  return found?.color || 'gray';
}

export function formatOSNumber(numero: string): string {
  if (!numero) return '';
  const parts = numero.split('-');
  return parts.length >= 3 ? parts[2] : numero;
}

/** Entrada da OS: timestamp de evento, gravado em UTC no backend. */
export function formatDataEntrada(data: string | Date | undefined): string {
  return formatData(data, '-');
}

/**
 * Previsão: dia escolhido pelo usuário, NÃO timestamp. Converter fuso aqui
 * jogaria o prazo para o dia anterior.
 */
export function formatDataPrevisao(data: string | Date | undefined): string {
  return formatDataPura(data, 'Não definida');
}

/**
 * Garantia de um item: "90 dias", "10.000 km" ou "90 dias / 10.000 km".
 * Vazio quando o item não tem nenhuma das duas — a garantia por item é
 * opcional, o mecânico preenche só quando quer.
 *
 * Vive aqui, e não em cada template, para a tela e as três vias impressas
 * dizerem exatamente a mesma frase.
 */
export function formatGarantiaItem(
  item: { garantia_dias?: number | null; garantia_km?: number | null },
): string {
  const partes: string[] = [];
  if (item.garantia_dias) partes.push(`${item.garantia_dias} dias`);
  if (item.garantia_km) partes.push(`${item.garantia_km.toLocaleString('pt-BR')} km`);
  return partes.join(' / ');
}

/**
 * Item REPROVADO não entra em soma nenhuma — o cliente recusou o serviço/peça.
 *
 * Esta regra já existia em SEIS lugares (backend, resumo da OS, modal de
 * finalizar, modal de pagamento e as três vias impressas) e cada cópia
 * divergia: o modal de finalizar somava o item reprovado e levava o valor para
 * o pagamento, cobrando do cliente exatamente o que ele tinha recusado.
 *
 * `!== 'REPROVADO'` e não `=== 'APROVADO'`: item de informática e OS anterior a
 * esta coluna não têm o campo e precisam continuar contando.
 */
export function itemContaNoTotal(item: { status_aprovacao?: string | null }): boolean {
  return item.status_aprovacao !== 'REPROVADO';
}

/** Soma `valor_total` só dos itens que contam. Use sempre no lugar de um reduce solto. */
export function somarItensDaOS(
  itens: ReadonlyArray<{ valor_total: number; status_aprovacao?: string | null }> | null | undefined,
): number {
  return (itens ?? [])
    .filter(itemContaNoTotal)
    .reduce((soma, item) => soma + item.valor_total, 0);
}
