/**
 * Onde aparecem os botões de CRIAR OS (Spec 03B da marcenaria, D3 e D5).
 *
 * Num segmento em que nenhum tipo de trabalho pode ser criado à mão (hoje, só
 * a marcenaria: a OS nasce da aprovação do orçamento), um botão "Nova OS"
 * abriria um formulário sem tipo possível, um beco sem saída. Estas funções
 * decidem, e as telas só as chamam. São puras de propósito: dá para testar
 * sem montar a tela inteira.
 *
 * Quem responde "o segmento permite criar OS à mão?" é `useTiposDeTrabalho`
 * (`podeCriarOSManual`); aqui só se aplica a resposta.
 */

/** Id do atalho "Criar OS" no menu rápido do MainLayout. */
export const ATALHO_NOVA_OS = 'nova-os';

/**
 * Botão do topo da tela de OS (OrdemServicoView).
 *   - aba Revisões: nunca teve botão (regra de antes);
 *   - aba Terceirizados (marcenaria, Spec 11B D13): só lê, nada a criar daqui;
 *   - aba Ordens ("Nova OS"): só se o segmento deixa criar à mão (D3);
 *   - aba Serviços ("Novo Serviço"): sempre; o catálogo não depende do tipo da OS (D5).
 */
export function mostrarBotaoAdicionar(aba: string, podeCriarOSManual: boolean): boolean {
  if (aba === 'revisoes') return false;               // regra de antes
  if (aba === 'terceirizados') return false;          // 11B D13: só lê
  if (aba === 'ordens') return podeCriarOSManual;     // "Nova OS"
  return true;                                        // "Novo Serviço"
}

/**
 * Atalhos do menu rápido: tira "Criar OS" onde a OS não pode ser criada à mão
 * (D3). Os outros atalhos ficam na mesma ordem e com o mesmo texto.
 */
export function filtrarAtalhos<T extends { id: string }>(atalhos: readonly T[], podeCriarOSManual: boolean): T[] {
  return atalhos.filter((atalho) => atalho.id !== ATALHO_NOVA_OS || podeCriarOSManual);
}

/** Id do atalho "Novo orçamento" (marcenaria, Spec 06B D4). */
export const ATALHO_NOVO_ORCAMENTO = 'novo-orcamento';

/**
 * Atalhos do menu rápido com a alternativa da marcenaria (Spec 06B D4, §7.10).
 *
 * Onde a OS NÃO é criada à mão, mas o segmento orça (orçamento técnico) e o
 * usuário pode gerir orçamentos, "Criar OS" vira `novoOrcamento`. Nos outros
 * segmentos, `podeCriarOSManual` é true e NADA muda (mesma regra de
 * `filtrarAtalhos`). Passe `novoOrcamento = null` quando não houver a
 * alternativa: aí o atalho só some, como antes.
 */
export function atalhosComOrcamento<T extends { id: string }>(
  atalhos: readonly T[],
  podeCriarOSManual: boolean,
  novoOrcamento: T | null,
): T[] {
  return atalhos.flatMap((atalho) => {
    if (atalho.id !== ATALHO_NOVA_OS || podeCriarOSManual) return [atalho];   // hoje: igual
    return novoOrcamento ? [novoOrcamento] : [];                              // marcenaria / sem nenhum
  });
}

/**
 * Botão "Novo orçamento" na aba Ordens da tela de OS (Spec 06B D4): aparece
 * no lugar de "Nova OS" quando ela não pode ser criada à mão e o usuário pode
 * criar orçamento.
 */
export function mostrarBotaoNovoOrcamento(aba: string, podeCriarOSManual: boolean, podeCriarOrcamento: boolean): boolean {
  return aba === 'ordens' && !podeCriarOSManual && podeCriarOrcamento;
}
