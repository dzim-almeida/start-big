/**
 * @fileoverview O que a API da separação devolve (Spec 10A §6), conferido pelo
 * zod. Quantidades em MILÉSIMOS (1,5 chapa = 1500), como o resto da
 * marcenaria; a tela converte só para mostrar.
 *
 * Nenhum campo de preço existe aqui (10A D22): a aba é do depósito.
 */
import { z } from 'zod';

const milesimos = z.number().int();

/** Os avisos de cada linha (a tela troca o código por uma frase, D8). */
export const ALERTAS_SEPARACAO = {
  semCobertura: 'SEM_COBERTURA',          // nem o estoque nem pedido cobrem
  estoqueNegativo: 'ESTOQUE_NEGATIVO',    // retirou sem saldo (10A D8)
  acimaDoSugerido: 'ACIMA_DO_SUGERIDO',   // retirou mais que o sugerido (10A D7)
} as const;

export const linhaSeparacaoSchema = z.object({
  item_id: z.number(),
  produto_id: z.number(),
  descricao: z.string(),
  codigo: z.string().nullable(),
  unidade: z.string(),
  localizacao: z.string().nullable(),
  planejado_milesimos: milesimos.nullable(),      // com a perda (orçado)
  sugerido_milesimos: milesimos.nullable(),       // arredondado para cima na unidade inteira
  quantidade_milesimos: milesimos,                // o que a OS vai consumir
  separada_milesimos: milesimos,                  // o que já saiu do estoque
  falta_milesimos: milesimos,                     // o que ainda sai
  concluida: z.boolean(),
  nao_usado: z.boolean(),
  no_estoque_milesimos: milesimos,                // quanto o estoque cobre PARA ESTA OS (fila do Compras)
  em_pedido_milesimos: milesimos,
  sem_cobertura_milesimos: milesimos,
  estoque_milesimos: milesimos,                   // o saldo do produto agora
  diferenca_bp: z.number().int().nullable(),      // orçado × real (+1200 = 12% acima)
  moveis: z.array(z.object({ nome: z.string(), ambiente: z.string(), planejado_milesimos: milesimos })),
  alertas: z.array(z.string()),                   // código novo do backend não quebra a tela
});
export type LinhaSeparacao = z.infer<typeof linhaSeparacaoSchema>;

export const separacaoSchema = z.object({
  os: z.object({ numero_os: z.string(), status: z.string(), editavel: z.boolean() }),
  linhas: z.array(linhaSeparacaoSchema),
  // Insumo cujo produto foi excluído: só informa (não baixa estoque, 10A D3).
  sem_cadastro: z.array(z.object({ descricao: z.string(), planejado_milesimos: milesimos })),
  resumo: z.object({ linhas: z.number(), concluidas: z.number(), com_falta: z.number() }),
});
export type Separacao = z.infer<typeof separacaoSchema>;

/** GET /separacao/ler: a linha do código lido e o fator (caixa de 10 = 10). */
export const leituraSchema = z.object({ fator: z.number().int().positive(), linha: linhaSeparacaoSchema });
export type Leitura = z.infer<typeof leituraSchema>;

/** GET /separacao/faltas: o que nem o estoque nem pedido cobrem (10A D18). */
export const faltasSchema = z.object({
  numero_os: z.string(),
  cliente: z.string().nullable(),
  itens: z.array(z.object({
    produto_id: z.number(),
    descricao: z.string(),
    unidade: z.string(),
    faltam_milesimos: milesimos,
    localizacao: z.string().nullable(),
    fornecedor: z.object({ id: z.number(), nome: z.string(), telefone: z.string().nullable() }).nullable(),
  })),
  gerado_em: z.string(),
});
export type FaltasDaOS = z.infer<typeof faltasSchema>;

/** GET /estoque/disponivel: por produto (a chave do JSON é o id em texto). */
export const disponivelSchema = z.record(z.string(), z.object({
  estoque_milesimos: milesimos,
  reservado_milesimos: milesimos,                 // todas as OS abertas (Compras)
  disponivel_milesimos: milesimos,                // pode ser negativo: falta comprar
}));
export type Disponivel = z.infer<typeof disponivelSchema>;
