/**
 * @fileoverview Constantes do orçamento de marcenaria (Spec 06B).
 *
 * Rótulos e cores de status, chaves de query do TanStack Query, sugestões de
 * nome de ambiente e atalhos do motivo de recusa. Nada aqui calcula valor:
 * os números vêm sempre da API (C8).
 */

/** Os status que a API devolve (06A §4.2). */
export type StatusOrcamento = 'RASCUNHO' | 'ENVIADO' | 'APROVADO' | 'RECUSADO' | 'VENCIDO' | 'SUBSTITUIDO';

/**
 * Rótulo e classes do selo de cada status (mesma paleta dos selos de OS).
 * As classes ficam escritas por inteiro para o Tailwind encontrá-las.
 */
export const STATUS_ORCAMENTO: Record<StatusOrcamento, { rotulo: string; classes: string }> = {
  RASCUNHO: { rotulo: 'Rascunho', classes: 'bg-zinc-100 text-zinc-700 border-zinc-200' },
  ENVIADO: { rotulo: 'Enviado', classes: 'bg-blue-50 text-blue-700 border-blue-200' },
  APROVADO: { rotulo: 'Aprovado', classes: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  RECUSADO: { rotulo: 'Recusado', classes: 'bg-red-50 text-red-700 border-red-200' },
  VENCIDO: { rotulo: 'Vencido', classes: 'bg-amber-50 text-amber-800 border-amber-200' },
  SUBSTITUIDO: { rotulo: 'Substituído', classes: 'bg-zinc-50 text-zinc-500 border-zinc-200' },
};

/** Chaves das queries: uma raiz só, para invalidar tudo do orçamento de uma vez. */
export const CHAVE_RAIZ = 'marcenaria-orcamentos' as const;
export const chaveLista = (filtros: unknown) => [CHAVE_RAIZ, 'lista', filtros] as const;
export const chaveContagens = () => [CHAVE_RAIZ, 'contagens'] as const;
export const chaveDetalhe = (id: number) => [CHAVE_RAIZ, 'detalhe', id] as const;
export const chaveVersoes = (id: number) => [CHAVE_RAIZ, 'versoes', id] as const;
export const chaveHistorico = (id: number) => [CHAVE_RAIZ, 'historico', id] as const;
export const chaveAnexos = (id: number) => [CHAVE_RAIZ, 'anexos', id] as const;
export const chaveProjetos = (clienteId: number) => [CHAVE_RAIZ, 'projetos', clienteId] as const;

/** Sugestões do nome do ambiente (D19): acelera, sem impedir texto livre. */
export const SUGESTOES_AMBIENTE = [
  'Cozinha',
  'Sala de estar',
  'Sala de jantar',
  'Dormitório casal',
  'Dormitório solteiro',
  'Closet',
  'Banheiro',
  'Lavabo',
  'Área de serviço',
  'Home office',
  'Varanda gourmet',
] as const;

/** Atalhos do motivo de recusa (D38): preenchem o texto, que continua livre. */
export const ATALHOS_RECUSA = ['Preço', 'Prazo', 'Fechou com outra marcenaria', 'Desistiu do projeto'] as const;

/** Limites iguais aos do backend (06A §5.1 e schemas). */
export const LIMITES = {
  nomeAmbiente: 80,
  nomeMovel: 120,
  descricaoMovel: 500,
  insumosPorMovel: 100,
  motivoRecusa: 500,
  legendaAnexo: 120,
  textoLongo: 4000,
  diasMin: 1,
  diasMax: 365,
} as const;

/** Rótulos dos campos do cabeçalho, para dizer ao usuário o que não foi salvo (D12). */
export const ROTULO_CAMPO: Record<string, string> = {
  cliente_id: 'Cliente',
  funcionario_id: 'Vendedor',
  objeto_id: 'Projeto',
  projeto_nome: 'Nome do projeto',
  endereco_obra: 'Endereço da obra',
  medicao_observacoes: 'Medidas e observações da medição',
  markup_bp: 'Markup',
  perda_bp: 'Perda',
  custo_hora_centavos: 'Custo por hora',
  rt_padrao_bp: 'RT padrão',
  instalacao_custo_centavos: 'Instalação',
  desconto: 'Desconto',
  sinal: 'Sinal',
  validade_dias: 'Validade',
  prazo_entrega_dias: 'Prazo de entrega',
  observacoes_proposta: 'Observações da proposta',
};

/** Tempo de espera do salvamento automático e da prévia (D6, D8). */
export const ESPERA_SALVAR_MS = 800;
export const ESPERA_PREVIA_MS = 400;
